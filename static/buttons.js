// Filter completed button
function toggleCompleted() {
    const filterButton = document.getElementById("filterButton");
    let filterActive = false;

    filterButton.addEventListener("click", () => {
        filterActive = !filterActive;
        const doneItems = document.querySelectorAll("#results .list-group-item-success");
        doneItems.forEach(item => {
            if (filterActive) {
                item.classList.add("hidden-done");
            } else {
                item.classList.remove("hidden-done");
            }
        });

        filterButton.innerText = filterActive ? "Show All" : "Hide Completed";
    });
};

// Results collapse button
function toggleCollapse(e) {
    const item = e.target.closest('.list-group-item-action');
    if (!item) return;
    if (e.target.tagName === "A") return;

    const arrow = item.querySelector('.happyarrow, .sadarrow');
    if (arrow) arrow.classList.toggle('down');

    const targetSel = item.getAttribute('data-target');
    if (!targetSel) return;
    const target = document.querySelector(targetSel);
    if (target) target.classList.toggle('show');
}

// Form toggle button
function toggleForm() {
    const form = document.getElementById('achForm');
    const toggle = document.getElementById('formToggle');

    toggle.addEventListener("click", () => {
        if (form.classList.contains('collapsed')) {
            form.classList.remove('collapsed');
            toggle.innerText = "▲ Hide Form";
            document.getElementById('title').classList.remove('collapsed');
            document.getElementById('title').classList.add('showing');
            setTimeout(() => {
                form.classList.remove('showing');
                document.getElementById('title').classList.remove('showing');
            }, 400);
        } else {
            form.classList.add('collapsed');
            toggle.innerText = "▼ Show Form";
            document.getElementById('title').classList.add('collapsed');
            
        }
    });
};


document.getElementById('results').addEventListener('click', toggleCollapse);
document.addEventListener("DOMContentLoaded", function () {
    toggleForm();
    toggleCompleted();
});