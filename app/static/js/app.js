document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('uploadForm');
  if (uploadForm) {
    const fileInput = document.getElementById('inventoryFile');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const alertBox = document.getElementById('uploadAlert');
    const clearInventoryBtn = document.getElementById('clearInventoryBtn');

    if (clearInventoryBtn) {
      clearInventoryBtn.addEventListener('click', async () => {
        const confirmed = window.confirm('This will delete all uploaded inventory data. Do you want to continue?');
        if (!confirmed) {
          return;
        }

        try {
          const response = await fetch('/api/inventory/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
          });

          const result = await response.json();
          if (!response.ok) {
            throw new Error(result.detail || 'Failed to clear inventory');
          }

          document.getElementById('totalRecords').textContent = '0';
          document.getElementById('successfulRecords').textContent = '0';
          document.getElementById('failedRecords').textContent = '0';
          document.getElementById('uploadTime').textContent = '0.00s';

          alertBox.innerHTML = `
            <div class="alert alert-warning">
              Master inventory cleared. ${result.deleted_records ?? 0} records removed.
            </div>
          `;
        } catch (error) {
          alertBox.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
        }
      });
    }

    uploadForm.addEventListener('submit', async (event) => {
      event.preventDefault();

      if (!fileInput.files || !fileInput.files[0]) {
        alertBox.innerHTML = '<div class="alert alert-warning">Please select an Excel file before uploading.</div>';
        return;
      }

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);

      progressBar.style.width = '0%';
      progressBar.textContent = '0%';
      progressText.textContent = 'Preparing upload';
      alertBox.innerHTML = '';

      let progressValue = 0;
      const updater = setInterval(() => {
        progressValue = Math.min(progressValue + 15, 90);
        progressBar.style.width = `${progressValue}%`;
        progressBar.textContent = `${progressValue}%`;
        progressText.textContent = 'Uploading and validating inventory';
      }, 250);

      try {
        const response = await fetch('/api/inventory/upload', {
          method: 'POST',
          body: formData,
        });

        const result = await response.json();
        if (!response.ok) {
          throw new Error(result.detail || 'Upload failed');
        }

        clearInterval(updater);
        progressBar.style.width = '100%';
        progressBar.textContent = '100%';
        progressText.textContent = 'Completed';

        document.getElementById('totalRecords').textContent = result.total_records ?? 0;
        document.getElementById('successfulRecords').textContent = result.successful_records ?? 0;
        document.getElementById('failedRecords').textContent = result.failed_records ?? 0;
        document.getElementById('uploadTime').textContent = result.upload_time ?? '0.00s';

        alertBox.innerHTML = `
          <div class="alert alert-success">
            Upload complete. Batch ID: <strong>${result.batch_id}</strong>
          </div>
        `;
      } catch (error) {
        clearInterval(updater);
        progressBar.style.width = '100%';
        progressBar.textContent = 'Failed';
        progressText.textContent = 'Upload failed';
        alertBox.innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
      }
    });
  }

  const reportTableBody = document.getElementById('reportTableBody');
  if (reportTableBody) {
    const state = {
      page: 1,
      per_page: 100,
      sort_by: 'main_code',
      sort_order: 'asc',
      main_code: '',
      child_code: '',
      description: '',
    };

    const mainCodeFilter = document.getElementById('mainCodeFilter');
    const childCodeFilter = document.getElementById('childCodeFilter');
    const descriptionFilter = document.getElementById('descriptionFilter');
    const resultsInfo = document.getElementById('resultsInfo');
    const paginationControls = document.getElementById('paginationControls');
    const exportBtn = document.getElementById('exportBtn');

    function readFilters() {
      const params = new URLSearchParams(window.location.search);
      state.main_code = params.get('main_code') || '';
      state.child_code = params.get('child_code') || '';
      state.description = params.get('description') || '';
      state.page = Number(params.get('page')) || 1;
      state.sort_by = params.get('sort_by') || 'main_code';
      state.sort_order = params.get('sort_order') || 'asc';
    }

    function writeFiltersToUrl() {
      const params = new URLSearchParams();
      if (state.main_code) params.set('main_code', state.main_code);
      if (state.child_code) params.set('child_code', state.child_code);
      if (state.description) params.set('description', state.description);
      if (state.sort_by) params.set('sort_by', state.sort_by);
      if (state.sort_order) params.set('sort_order', state.sort_order);
      params.set('page', String(state.page));
      const url = new URL(window.location.href);
      url.search = params.toString();
      window.history.replaceState({}, '', url);
    }

    function buildQueryString() {
      const params = new URLSearchParams();
      if (state.main_code) params.set('main_code', state.main_code);
      if (state.child_code) params.set('child_code', state.child_code);
      if (state.description) params.set('description', state.description);
      params.set('page', String(state.page));
      params.set('per_page', String(state.per_page));
      params.set('sort_by', state.sort_by);
      params.set('sort_order', state.sort_order);
      return params.toString();
    }

    function renderTable(rows) {
      if (!rows || rows.length === 0) {
        reportTableBody.innerHTML = `
          <tr>
            <td colspan="6" class="text-center text-muted py-4">No records found</td>
          </tr>
        `;
        return;
      }

      reportTableBody.innerHTML = rows.map((row) => `
        <tr>
          <td>${row.main_code ?? ''}</td>
          <td>${row.child_code ?? ''}</td>
          <td>${row.description ?? ''}</td>
          <td>${Number(row.available_qty ?? 0).toFixed(2)}</td>
          <td>${Number(row.set_qty ?? 0).toFixed(2)}</td>
          <td>${Number(row.loose_qty ?? 0).toFixed(2)}</td>
        </tr>
      `).join('');
    }

    function renderPagination(page, totalPages, totalRecords, perPage) {
      const pages = [];
      const startPage = Math.max(1, page - 2);
      const endPage = Math.min(totalPages, page + 2);

      for (let i = startPage; i <= endPage; i += 1) {
        pages.push(i);
      }

      paginationControls.innerHTML = `
        <li class="page-item ${page === 1 ? 'disabled' : ''}">
          <button class="page-link" data-page="1">First</button>
        </li>
        <li class="page-item ${page === 1 ? 'disabled' : ''}">
          <button class="page-link" data-page="${Math.max(1, page - 1)}">Previous</button>
        </li>
        ${pages.map((pageNumber) => `
          <li class="page-item ${pageNumber === page ? 'active' : ''}">
            <button class="page-link" data-page="${pageNumber}">${pageNumber}</button>
          </li>
        `).join('')}
        <li class="page-item ${page >= totalPages ? 'disabled' : ''}">
          <button class="page-link" data-page="${Math.min(totalPages, page + 1)}">Next</button>
        </li>
        <li class="page-item ${page >= totalPages ? 'disabled' : ''}">
          <button class="page-link" data-page="${totalPages}">Last</button>
        </li>
      `;

      const showingStart = totalRecords === 0 ? 0 : (page - 1) * perPage + 1;
      const showingEnd = Math.min(page * perPage, totalRecords);
      resultsInfo.textContent = `Showing ${showingStart}-${showingEnd} of ${totalRecords} records`;

      paginationControls.querySelectorAll('[data-page]').forEach((button) => {
        button.addEventListener('click', () => {
          const nextPage = Number(button.dataset.page);
          if (!Number.isNaN(nextPage) && nextPage >= 1 && nextPage <= totalPages) {
            state.page = nextPage;
            writeFiltersToUrl();
            loadReports();
          }
        });
      });
    }

    async function loadReports() {
      const params = buildQueryString();
      const response = await fetch(`/api/reports?${params}`);
      const payload = await response.json();
      renderTable(payload.records);
      renderPagination(payload.page, payload.total_pages, payload.total_records, payload.per_page);
      writeFiltersToUrl();
    }

    function updateFilterValues() {
      mainCodeFilter.value = state.main_code;
      childCodeFilter.value = state.child_code;
      descriptionFilter.value = state.description;
    }

    document.getElementById('applyFiltersBtn').addEventListener('click', () => {
      state.main_code = mainCodeFilter.value.trim();
      state.child_code = childCodeFilter.value.trim();
      state.description = descriptionFilter.value.trim();
      state.page = 1;
      loadReports();
    });

    document.getElementById('clearFiltersBtn').addEventListener('click', () => {
      state.main_code = '';
      state.child_code = '';
      state.description = '';
      state.page = 1;
      updateFilterValues();
      loadReports();
    });

    document.querySelectorAll('[data-sort]').forEach((header) => {
      header.addEventListener('click', () => {
        const nextSort = header.dataset.sort;
        if (state.sort_by === nextSort) {
          state.sort_order = state.sort_order === 'asc' ? 'desc' : 'asc';
        } else {
          state.sort_by = nextSort;
          state.sort_order = 'asc';
        }
        state.page = 1;
        loadReports();
      });
    });

    exportBtn.addEventListener('click', () => {
      const exportParams = new URLSearchParams(buildQueryString());
      exportParams.delete('page');
      exportParams.delete('per_page');
      window.location.href = `/api/reports/export?${exportParams.toString()}`;
    });

    readFilters();
    updateFilterValues();
    loadReports();
  }

  const reviewTableBody = document.getElementById('reviewTableBody');
  if (reviewTableBody) {
    const reviewState = {
      page: 1,
      per_page: 100,
      sort_by: 'main_code',
      sort_order: 'asc',
      main_code: '',
      child_code: '',
      description: '',
    };

    const reviewResultsInfo = document.getElementById('reviewResultsInfo');
    const reviewPaginationControls = document.getElementById('reviewPaginationControls');
    const reviewExportBtn = document.getElementById('reviewExportBtn');

    function buildReviewQueryString() {
      const params = new URLSearchParams();
      if (reviewState.main_code) params.set('main_code', reviewState.main_code);
      if (reviewState.child_code) params.set('child_code', reviewState.child_code);
      if (reviewState.description) params.set('description', reviewState.description);
      params.set('page', String(reviewState.page));
      params.set('per_page', String(reviewState.per_page));
      params.set('sort_by', reviewState.sort_by);
      params.set('sort_order', reviewState.sort_order);
      return params.toString();
    }

    function renderReviewTable(rows) {
      if (!rows || rows.length === 0) {
        reviewTableBody.innerHTML = `
          <tr>
            <td colspan="6" class="text-center text-muted py-4">No review records found</td>
          </tr>
        `;
        return;
      }

      reviewTableBody.innerHTML = rows.map((row) => `
        <tr>
          <td>${row.main_code ?? ''}</td>
          <td>${row.description ?? ''}</td>
          <td>${Number(row.set_size ?? 0)}</td>
          <td>${Number(row.missing_qty ?? 0)}</td>
          <td>${row.short_component ?? ''}</td>
          <td>${JSON.stringify(row.component_quantities ?? {})}</td>
        </tr>
      `).join('');
    }

    function renderReviewPagination(page, totalPages, totalRecords, perPage) {
      const pages = [];
      const startPage = Math.max(1, page - 2);
      const endPage = Math.min(totalPages, page + 2);

      for (let i = startPage; i <= endPage; i += 1) {
        pages.push(i);
      }

      reviewPaginationControls.innerHTML = `
        <li class="page-item ${page === 1 ? 'disabled' : ''}">
          <button class="page-link" data-review-page="1">First</button>
        </li>
        <li class="page-item ${page === 1 ? 'disabled' : ''}">
          <button class="page-link" data-review-page="${Math.max(1, page - 1)}">Previous</button>
        </li>
        ${pages.map((pageNumber) => `
          <li class="page-item ${pageNumber === page ? 'active' : ''}">
            <button class="page-link" data-review-page="${pageNumber}">${pageNumber}</button>
          </li>
        `).join('')}
        <li class="page-item ${page >= totalPages ? 'disabled' : ''}">
          <button class="page-link" data-review-page="${Math.min(totalPages, page + 1)}">Next</button>
        </li>
        <li class="page-item ${page >= totalPages ? 'disabled' : ''}">
          <button class="page-link" data-review-page="${totalPages}">Last</button>
        </li>
      `;

      const showingStart = totalRecords === 0 ? 0 : (page - 1) * perPage + 1;
      const showingEnd = Math.min(page * perPage, totalRecords);
      reviewResultsInfo.textContent = `Showing ${showingStart}-${showingEnd} of ${totalRecords} records`;

      reviewPaginationControls.querySelectorAll('[data-review-page]').forEach((button) => {
        button.addEventListener('click', () => {
          const nextPage = Number(button.dataset.reviewPage);
          if (!Number.isNaN(nextPage) && nextPage >= 1 && nextPage <= totalPages) {
            reviewState.page = nextPage;
            loadReviewRows();
          }
        });
      });
    }

    async function loadReviewRows() {
      const params = buildReviewQueryString();
      const response = await fetch(`/api/reports/review?${params}`);
      const payload = await response.json();
      renderReviewTable(payload.records);
      renderReviewPagination(payload.page, payload.total_pages, payload.total_records, payload.per_page);
    }

    reviewExportBtn.addEventListener('click', () => {
      const exportParams = new URLSearchParams(buildReviewQueryString());
      exportParams.delete('page');
      exportParams.delete('per_page');
      window.location.href = `/api/reports/review/export?${exportParams.toString()}`;
    });

    const mainFilterInputs = {
      main_code: document.getElementById('mainCodeFilter'),
      child_code: document.getElementById('childCodeFilter'),
      description: document.getElementById('descriptionFilter'),
    };

    const syncReviewFilters = () => {
      reviewState.main_code = mainFilterInputs.main_code.value.trim();
      reviewState.child_code = mainFilterInputs.child_code.value.trim();
      reviewState.description = mainFilterInputs.description.value.trim();
      reviewState.page = 1;
      loadReviewRows();
    };

    mainFilterInputs.main_code.addEventListener('change', syncReviewFilters);
    mainFilterInputs.child_code.addEventListener('change', syncReviewFilters);
    mainFilterInputs.description.addEventListener('change', syncReviewFilters);

    document.getElementById('applyFiltersBtn').addEventListener('click', syncReviewFilters);
    document.getElementById('clearFiltersBtn').addEventListener('click', () => {
      mainFilterInputs.main_code.value = '';
      mainFilterInputs.child_code.value = '';
      mainFilterInputs.description.value = '';
      syncReviewFilters();
    });

    loadReviewRows();
  }
});
