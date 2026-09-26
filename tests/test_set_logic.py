from app.core.database import SessionLocal
from app.models.inventory import InventoryMaster
from app.repositories.inventory_repository import InventoryRepository
from app.services.set_calculation import calculate_set_inventory, find_one_qty_short_sets
from app.services.upload_service import InventoryUploadService


def test_find_one_qty_short_sets_detects_single_unit_gap_and_missing_child():
    rows = [
        {"Item (Child code)": "5101011004119-01/04", "description": "Chair Set", "Onhand": 5},
        {"Item (Child code)": "5101011004119-02/04", "description": "Chair Set", "Onhand": 4},
        {"Item (Child code)": "5101011004119-03/04", "description": "Chair Set", "Onhand": 5},
        {"Item (Child code)": "5101011004119-04/04", "description": "Chair Set", "Onhand": 5},
        {"Item": "5110900500229-01/02", "Description": "Second Set", "On Hand": 1},
    ]

    result = find_one_qty_short_sets(rows)

    assert result == [
        {
            "main_code": "5101011004119",
            "description": "Chair Set",
            "set_size": 4,
            "missing_qty": 1,
            "short_component": "5101011004119-02/04",
            "component_quantities": {
                "5101011004119-01/04": 5,
                "5101011004119-02/04": 4,
                "5101011004119-03/04": 5,
                "5101011004119-04/04": 5,
            },
        },
        {
            "main_code": "5110900500229",
            "description": "Second Set",
            "set_size": 2,
            "missing_qty": 1,
            "short_component": "5110900500229-02/02",
            "component_quantities": {
                "5110900500229-01/02": 1,
            },
        },
    ]


def test_find_one_qty_short_sets_ignores_sets_needing_more_than_one_total_qty():
    rows = [
        {"Item (Child code)": "5121910200030-01/03", "description": "Triple Set", "Onhand": 1},
        {"Item (Child code)": "5121910200030-02/03", "description": "Triple Set", "Onhand": 2},
        {"Item (Child code)": "5121910200030-03/03", "description": "Triple Set", "Onhand": 1},
    ]

    result = find_one_qty_short_sets(rows)

    assert result == []


def test_set_inventory_calculation_for_parent_group():
    rows = [
        {"Item (Child code)": "5101011004119-01/04", "description": "Chair Set", "LPN": "LPN1", "Location": "A1", "Onhand": 5},
        {"Item (Child code)": "5101011004119-02/04", "description": "Chair Set", "LPN": "LPN2", "Location": "A2", "Onhand": 5},
        {"Item (Child code)": "5101011004119-03/04", "description": "Chair Set", "LPN": "LPN3", "Location": "A3", "Onhand": 4},
        {"Item (Child code)": "5101011004119-04/04", "description": "Chair Set", "LPN": "LPN4", "Location": "A4", "Onhand": 6},
    ]

    result = calculate_set_inventory(rows)

    assert result == [
        {
            "Main Code": "5101011004119",
            "Child Code": "5101011004119-01/04",
            "Description": "Chair Set",
            "Available Qty": 5,
            "Set Qty": 4,
            "Loose Qty": 1,
        },
        {
            "Main Code": "5101011004119",
            "Child Code": "5101011004119-02/04",
            "Description": "Chair Set",
            "Available Qty": 5,
            "Set Qty": 4,
            "Loose Qty": 1,
        },
        {
            "Main Code": "5101011004119",
            "Child Code": "5101011004119-03/04",
            "Description": "Chair Set",
            "Available Qty": 4,
            "Set Qty": 4,
            "Loose Qty": 0,
        },
        {
            "Main Code": "5101011004119",
            "Child Code": "5101011004119-04/04",
            "Description": "Chair Set",
            "Available Qty": 6,
            "Set Qty": 4,
            "Loose Qty": 2,
        },
    ]


def test_set_inventory_keeps_non_set_items_as_direct_rows():
    rows = [
        {"Item (Child code)": "ABC123", "description": "Lamp", "LPN": "L1", "Location": "B1", "Onhand": 3},
    ]

    result = calculate_set_inventory(rows)

    assert result == [
        {
            "Main Code": "ABC123",
            "Child Code": "ABC123",
            "Description": "Lamp",
            "Available Qty": 3,
            "Set Qty": 3,
            "Loose Qty": 0,
        }
    ]


def test_set_inventory_with_warehouse_headers_and_standalone_parent_items():
    rows = [
        {"Item": "5110900500281-01/04", "Description": "Chair Set", "Location": "A1", "LPN": "LPN1", "On Hand": 5},
        {"Item": "5110900500281-02/04", "Description": "Chair Set", "Location": "A2", "LPN": "LPN2", "On Hand": 5},
        {"Item": "5110900500281-03/04", "Description": "Chair Set", "Location": "A3", "LPN": "LPN3", "On Hand": 4},
        {"Item": "5110900500281-04/04", "Description": "Chair Set", "Location": "A4", "LPN": "LPN4", "On Hand": 6},
        {"Item": "5110900500281", "Description": "Standalone parent", "Location": "B1", "LPN": "LPN5", "On Hand": 2},
    ]

    result = calculate_set_inventory(rows)

    assert result == [
        {
            "Main Code": "5110900500281",
            "Child Code": "5110900500281-01/04",
            "Description": "Chair Set",
            "Available Qty": 5,
            "Set Qty": 4,
            "Loose Qty": 1,
        },
        {
            "Main Code": "5110900500281",
            "Child Code": "5110900500281-02/04",
            "Description": "Chair Set",
            "Available Qty": 5,
            "Set Qty": 4,
            "Loose Qty": 1,
        },
        {
            "Main Code": "5110900500281",
            "Child Code": "5110900500281-03/04",
            "Description": "Chair Set",
            "Available Qty": 4,
            "Set Qty": 4,
            "Loose Qty": 0,
        },
        {
            "Main Code": "5110900500281",
            "Child Code": "5110900500281-04/04",
            "Description": "Chair Set",
            "Available Qty": 6,
            "Set Qty": 4,
            "Loose Qty": 2,
        },
        {
            "Main Code": "5110900500281",
            "Child Code": "5110900500281",
            "Description": "Standalone parent",
            "Available Qty": 2,
            "Set Qty": 2,
            "Loose Qty": 0,
        },
    ]


def test_set_inventory_accepts_qty_alias_column_name():
    rows = [
        {"Item": "5110900500281-01/04", "Description": "Chair Set", "Location": "A1", "LPN": "LPN1", "Qty": 5},
        {"Item": "5110900500281-02/04", "Description": "Chair Set", "Location": "A2", "LPN": "LPN2", "Qty": 5},
        {"Item": "5110900500281", "Description": "Standalone parent", "Location": "B1", "LPN": "LPN5", "Qty": 2},
    ]

    result = calculate_set_inventory(rows)

    assert result[0]["Main Code"] == "5110900500281"
    assert result[0]["Child Code"] == "5110900500281-01/04"
    assert result[0]["Available Qty"] == 5
    assert result[0]["Set Qty"] == 0
    assert result[0]["Loose Qty"] == 5
    assert result[-1] == {
        "Main Code": "5110900500281",
        "Child Code": "5110900500281",
        "Description": "Standalone parent",
        "Available Qty": 2,
        "Set Qty": 2,
        "Loose Qty": 0,
    }


def test_set_inventory_prefers_qty_over_available_and_on_hand_when_both_columns_exist():
    rows = [
        {"Item": "5110900500281-01/04", "Description": "Chair Set", "Location": "A1", "LPN": "LPN1", "Qty": 49, "On Hand": 100, "Available Qty": 1025},
        {"Item": "5110900500281-02/04", "Description": "Chair Set", "Location": "A2", "LPN": "LPN2", "Qty": 49, "On Hand": 100, "Available Qty": 1025},
        {"Item": "5110900500281-03/04", "Description": "Chair Set", "Location": "A3", "LPN": "LPN3", "Qty": 49, "On Hand": 100, "Available Qty": 1025},
        {"Item": "5110900500281-04/04", "Description": "Chair Set", "Location": "A4", "LPN": "LPN4", "Qty": 49, "On Hand": 100, "Available Qty": 1025},
    ]

    result = calculate_set_inventory(rows)

    assert all(row["Available Qty"] == 49 for row in result[:4])
    assert all(row["Set Qty"] == 49 for row in result[:4])
    assert all(row["Loose Qty"] == 0 for row in result[:4])


def test_upload_service_uses_qty_field_as_source_of_truth():
    service = InventoryUploadService()
    rows = [
        {"Item": "ABC123", "Description": "Standalone item", "Location": "A1", "LPN": "LPN1", "Qty": 49, "On Hand": 100, "Available Qty": 1025},
    ]

    valid_rows, failed = service._prepare_valid_rows(rows)

    assert failed == 0
    assert valid_rows == [{
        "main_code": "ABC123",
        "child_code": "ABC123",
        "description": "Standalone item",
        "available_qty": 49.0,
        "set_qty": 49.0,
        "loose_qty": 0.0,
    }]


def test_upload_service_ignores_available_column_when_qty_is_present():
    service = InventoryUploadService()
    rows = [
        {"Item": "5110801701183", "Description": "RESORTFACE TOWEL", "Location": "A1", "LPN": "LPN1", "Qty": 49, "Available": 1254},
    ]

    valid_rows, failed = service._prepare_valid_rows(rows)

    assert failed == 0
    assert valid_rows == [{
        "main_code": "5110801701183",
        "child_code": "5110801701183",
        "description": "RESORTFACE TOWEL",
        "available_qty": 49.0,
        "set_qty": 49.0,
        "loose_qty": 0.0,
    }]


def test_inventory_repository_clear_inventory_records_removes_all_master_rows():
    db = SessionLocal()
    try:
        db.query(InventoryMaster).delete(synchronize_session=False)
        db.add_all([
            InventoryMaster(main_code="A", child_code="A-01/02", description="Sample", available_qty=10, set_qty=10, loose_qty=0, upload_batch_id=1),
            InventoryMaster(main_code="B", child_code="B", description="Standalone", available_qty=5, set_qty=5, loose_qty=0, upload_batch_id=1),
        ])
        db.commit()

        deleted = InventoryRepository().clear_inventory_records(db)

        assert deleted == 2
        assert db.query(InventoryMaster).count() == 0
    finally:
        db.query(InventoryMaster).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_set_inventory_keeps_non_component_skus_as_full_set_quantity():
    rows = [
        {"Item": "2024417231084", "Description": "Standalone item", "Location": "A1", "LPN": "LPN1", "On Hand": 7},
        {"Item": "2468013043762", "Description": "Standalone item 2", "Location": "A2", "LPN": "LPN2", "On Hand": 3},
    ]

    result = calculate_set_inventory(rows)

    assert result == [
        {
            "Main Code": "2024417231084",
            "Child Code": "2024417231084",
            "Description": "Standalone item",
            "Available Qty": 7,
            "Set Qty": 7,
            "Loose Qty": 0,
        },
        {
            "Main Code": "2468013043762",
            "Child Code": "2468013043762",
            "Description": "Standalone item 2",
            "Available Qty": 3,
            "Set Qty": 3,
            "Loose Qty": 0,
        },
    ]


def test_report_service_normalizes_standalone_row_set_qty():
    from app.services.report_service import ReportService

    normalized = ReportService._normalize_report_row({
        "main_code": "2024417231084",
        "child_code": "2024417231084",
        "description": "Standalone item",
        "available_qty": 7,
        "set_qty": 0,
        "loose_qty": 0,
    })

    assert normalized["set_qty"] == 7
    assert normalized["loose_qty"] == 0


def test_set_inventory_requires_all_expected_components_before_counting_as_set():
    rows = [
        {"Item (Child code)": "5121101208890-01/04", "description": "Set item", "Onhand": 6},
        {"Item (Child code)": "5121101208890-02/04", "description": "Set item", "Onhand": 5},
        {"Item (Child code)": "5121101208890-03/04", "description": "Set item", "Onhand": 2},
    ]

    result = calculate_set_inventory(rows)

    assert result == [
        {
            "Main Code": "5121101208890",
            "Child Code": "5121101208890-01/04",
            "Description": "Set item",
            "Available Qty": 6,
            "Set Qty": 0,
            "Loose Qty": 6,
        },
        {
            "Main Code": "5121101208890",
            "Child Code": "5121101208890-02/04",
            "Description": "Set item",
            "Available Qty": 5,
            "Set Qty": 0,
            "Loose Qty": 5,
        },
        {
            "Main Code": "5121101208890",
            "Child Code": "5121101208890-03/04",
            "Description": "Set item",
            "Available Qty": 2,
            "Set Qty": 0,
            "Loose Qty": 2,
        },
    ]
