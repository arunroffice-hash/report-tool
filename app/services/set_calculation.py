import re
from collections import defaultdict
from typing import Any


def _parse_item_code(item_value: Any) -> tuple[str | None, int | None, int | None, bool]:
    """Parse a component item like '5101011004119-02/04' into parent, sequence and set size."""
    value = str(item_value).strip()
    if not value:
        return None, None, None, False

    match = re.match(r"^(.*)-([0-9]+)/([0-9]+)$", value)
    if not match:
        return None, None, None, False

    parent_code = match.group(1).strip()
    sequence_no = int(match.group(2))
    set_size = int(match.group(3))
    return parent_code, sequence_no, set_size, bool(parent_code)


def _read_quantity(row: dict[str, Any]) -> float:
    """Use the uploaded Qty column as the source of truth and only fall back to other quantity fields if Qty is missing."""
    for key in ("Qty", "Quantity", "On Hand", "Onhand", "Available Qty", "Available", "available_qty"):
        if row.get(key) is not None:
            value = row.get(key)
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def find_one_qty_short_sets(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return parent sets that are exactly one unit away from being complete.

    This is a review-only flag for near-complete sets, separate from the normal
    set aggregation. A set qualifies when every present component is either at the
    current maximum quantity or exactly one less than that maximum, and the deficit
    is limited to one unit. This covers both cases:
    - 5, 4, 5, 5 for a 4-piece set
    - 1, 0 for a 2-piece set
    """
    grouped_components: dict[tuple[str, str], float] = defaultdict(float)
    grouped_descriptions: dict[str, str] = {}
    parent_set_size: dict[str, int] = {}

    for row in rows:
        item_value = (
            row.get("Item")
            or row.get("Item (Child code)")
            or row.get("Child Code")
            or row.get("Main Code")
            or ""
        )
        description = str(row.get("Description") or row.get("description") or "").strip()
        qty = _read_quantity(row)

        parent_code, sequence_no, set_size, is_set_component = _parse_item_code(item_value)
        if is_set_component and parent_code:
            grouped_components[(parent_code, str(item_value).strip())] += qty
            grouped_descriptions[(parent_code, str(item_value).strip())] = description or grouped_descriptions.get(
                (parent_code, str(item_value).strip()), ""
            )
            if set_size:
                parent_set_size[parent_code] = max(parent_set_size.get(parent_code, set_size), set_size)

    review_rows: list[dict[str, Any]] = []
    for parent_code in sorted(parent_set_size):
        components = sorted(
            [(child_code, qty) for (group_parent, child_code), qty in grouped_components.items() if group_parent == parent_code],
            key=lambda x: x[0],
        )
        if not components:
            continue

        set_size = parent_set_size[parent_code]
        if set_size <= 0:
            continue

        quantities = {child_code: qty for child_code, qty in components}
        max_qty = max(quantities.values()) if quantities else 0
        expected_sequences = set(range(1, set_size + 1))
        present_sequences = {
            int(_parse_item_code(child_code)[1])
            for child_code in quantities
            if _parse_item_code(child_code)[1] is not None
        }
        missing_sequences = sorted(expected_sequences - present_sequences)

        if max_qty <= 0:
            continue

        total_shortfall = sum(max(max_qty - qty, 0) for qty in quantities.values())
        if missing_sequences:
            total_shortfall += len(missing_sequences) * max_qty

        if total_shortfall != 1:
            continue

        if missing_sequences:
            short_component = f"{parent_code}-{missing_sequences[0]:02d}/{set_size:02d}"
        else:
            short_component = min(quantities, key=lambda child_code: quantities[child_code])

        review_rows.append(
            {
                "main_code": parent_code,
                "description": grouped_descriptions.get((parent_code, short_component), "")
                or grouped_descriptions.get((parent_code, min(quantities, key=lambda child_code: quantities[child_code])), ""),
                "set_size": set_size,
                "missing_qty": 1,
                "short_component": short_component,
                "component_quantities": {
                    child_code: float(qty) for child_code, qty in quantities.items()
                },
            }
        )

    return review_rows


def calculate_set_inventory(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate stocktake rows into set-aware source data.

    Rules:
    - Handle set-based items such as 5101011004119-01/04, 02/04, 03/04, 04/04.
    - Calculate set quantity as the minimum quantity across components of the same parent set.
    - Mark extra quantity above the complete set count as loose quantity for each component.
    - Keep non-set items as direct rows with Set Qty = 0 and Loose Qty = 0.
    - A plain parent item like 5110900500281 is treated as a standalone non-child row.
    """
    grouped_components: dict[tuple[str, str], float] = defaultdict(float)
    grouped_descriptions: dict[str, str] = {}
    direct_components: dict[str, float] = defaultdict(float)
    direct_descriptions: dict[str, str] = {}
    parent_set_size: dict[str, int] = {}
    parent_sequences: dict[str, set[int]] = defaultdict(set)

    for row in rows:
        item_value = (
            row.get("Item")
            or row.get("Item (Child code)")
            or row.get("Child Code")
            or row.get("Main Code")
            or ""
        )
        description = str(row.get("Description") or row.get("description") or "").strip()
        qty = _read_quantity(row)

        parent_code, sequence_no, set_size, is_set_component = _parse_item_code(item_value)
        if is_set_component and parent_code:
            grouped_components[(parent_code, str(item_value).strip())] += qty
            grouped_descriptions[(parent_code, str(item_value).strip())] = description or grouped_descriptions.get(
                (parent_code, str(item_value).strip()), ""
            )
            if set_size:
                parent_set_size[parent_code] = max(parent_set_size.get(parent_code, set_size), set_size)
            if sequence_no is not None:
                parent_sequences[parent_code].add(sequence_no)
        else:
            direct_components[str(item_value).strip()] += qty
            direct_descriptions[str(item_value).strip()] = description or direct_descriptions.get(
                str(item_value).strip(), ""
            )

    results: list[dict[str, Any]] = []

    parent_groups: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (parent_code, child_code), total_qty in grouped_components.items():
        parent_groups[parent_code].append((child_code, total_qty))

    for parent_code, components in parent_groups.items():
        set_size = parent_set_size.get(parent_code, 0)
        expected_sequences = set(range(1, set_size + 1)) if set_size else set()
        present_sequences = {int(_parse_item_code(child_code)[1]) for child_code, _ in components if _parse_item_code(child_code)[1] is not None}
        is_complete_set = bool(set_size) and expected_sequences.issubset(present_sequences)

        if not set_size:
            set_quantity = min(qty for _, qty in components) if components else 0
            is_complete_set = True
        else:
            set_quantity = min(qty for _, qty in components) if components else 0

        if not is_complete_set:
            set_quantity = 0

        for child_code, total_qty in sorted(components, key=lambda x: x[0]):
            if not is_complete_set:
                loose_qty = total_qty
            else:
                loose_qty = max(total_qty - set_quantity, 0)
                if total_qty < set_quantity:
                    loose_qty = 0
            results.append(
                {
                    "Main Code": parent_code,
                    "Child Code": child_code,
                    "Description": grouped_descriptions.get((parent_code, child_code), ""),
                    "Available Qty": total_qty,
                    "Set Qty": set_quantity,
                    "Loose Qty": loose_qty,
                }
            )

    for item_code, total_qty in sorted(direct_components.items()):
        results.append(
            {
                "Main Code": item_code,
                "Child Code": item_code,
                "Description": direct_descriptions.get(item_code, ""),
                "Available Qty": total_qty,
                "Set Qty": total_qty,
                "Loose Qty": 0,
            }
        )

    return sorted(
        results,
        key=lambda r: (
            str(r["Main Code"]),
            0 if "-" in str(r["Child Code"]) else 1,
            str(r["Child Code"]),
        ),
    )
