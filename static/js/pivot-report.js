document.addEventListener('DOMContentLoaded', function () {
    // Non-Financial Keterangan Elements
    const nonFinanceSearchInput = document.getElementById('nonFinanceSearch');
    const nonFinanceList = document.getElementById('nonFinanceList');
    const nonFinanceItems = nonFinanceList.getElementsByClassName('keterangan-item-non-finance');
    const selectAllNonFinanceCheckbox = document.getElementById('selectAllNonFinance');

    // Financial Keterangan Elements
    const financeSearchInput = document.getElementById('financeSearch');
    const financeList = document.getElementById('financeList');
    const financeItems = financeList.getElementsByClassName('keterangan-item-finance');
    const selectAllFinanceCheckbox = document.getElementById('selectAllFinance');

    // Function to handle search and filter
    function handleSearch(searchInput, items, selectAllCheckbox) {
        const filter = searchInput.value.toLowerCase();
        let allVisibleChecked = true;
        for (let i = 0; i < items.length; i++) {
            const label = items[i].getElementsByTagName('label')[0];
            const txtValue = label.textContent || label.innerText;
            if (txtValue.toLowerCase().indexOf(filter) > -1) {
                items[i].style.display = "";
                const checkbox = items[i].querySelector('input[type="checkbox"]');
                if (!checkbox.checked) {
                    allVisibleChecked = false;
                }
            } else {
                items[i].style.display = "none";
                // Uncheck the checkbox if it's hidden
                items[i].querySelector('input[type="checkbox"]').checked = false;
            }
        }
        // Update "Select All" checkbox based on visible items
        selectAllCheckbox.checked = allVisibleChecked;
    }

    // Event Listeners for Non-Financial Search
    nonFinanceSearchInput.addEventListener('keyup', function () {
        handleSearch(nonFinanceSearchInput, nonFinanceItems, selectAllNonFinanceCheckbox);
    });

    // Event Listeners for Financial Search
    financeSearchInput.addEventListener('keyup', function () {
        handleSearch(financeSearchInput, financeItems, selectAllFinanceCheckbox);
    });

    // Function to handle Select All
    function handleSelectAll(selectAllCheckbox, items) {
        const isChecked = selectAllCheckbox.checked;
        for (let i = 0; i < items.length; i++) {
            if (items[i].style.display !== "none") { // Only select visible checkboxes
                items[i].querySelector('input[type="checkbox"]').checked = isChecked;
            }
        }
    }

    // Select All for Non-Financial Keterangan
    selectAllNonFinanceCheckbox.addEventListener('change', function () {
        handleSelectAll(selectAllNonFinanceCheckbox, nonFinanceItems);
    });

    // Select All for Financial Keterangan
    selectAllFinanceCheckbox.addEventListener('change', function () {
        handleSelectAll(selectAllFinanceCheckbox, financeItems);
    });

    // Function to update Select All based on individual checkbox changes
    function updateSelectAll(selectAllCheckbox, items) {
        let allChecked = true;
        for (let i = 0; i < items.length; i++) {
            if (items[i].style.display !== "none") {
                const checkbox = items[i].querySelector('input[type="checkbox"]');
                if (!checkbox.checked) {
                    allChecked = false;
                    break;
                }
            }
        }
        selectAllCheckbox.checked = allChecked;
    }

    // Event Listeners for Individual Non-Financial Checkboxes
    for (let i = 0; i < nonFinanceItems.length; i++) {
        const checkbox = nonFinanceItems[i].querySelector('input[type="checkbox"]');
        checkbox.addEventListener('change', function () {
            if (!this.checked) {
                selectAllNonFinanceCheckbox.checked = false;
            } else {
                updateSelectAll(selectAllNonFinanceCheckbox, nonFinanceItems);
            }
        });
    }

    // Event Listeners for Individual Financial Checkboxes
    for (let i = 0; i < financeItems.length; i++) {
        const checkbox = financeItems[i].querySelector('input[type="checkbox"]');
        checkbox.addEventListener('change', function () {
            if (!this.checked) {
                selectAllFinanceCheckbox.checked = false;
            } else {
                updateSelectAll(selectAllFinanceCheckbox, financeItems);
            }
        });
    }
});
