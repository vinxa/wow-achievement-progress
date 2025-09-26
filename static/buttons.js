
// Filter completed button
let filterActive = false;
function filterResults(filterActive) {
    const doneItems = document.querySelectorAll("#results .list-group-item-success");
    doneItems.forEach(item => {
        if (filterActive) {
            item.classList.add("hidden-done");
        } else {
            item.classList.remove("hidden-done");
        }
    });

    filterButton.innerText = filterActive ? "Show All" : "Hide Completed";
}
window.filterResults = filterResults;
function toggleCompleted() {
    const filterButton = document.getElementById("filterButton");

    filterButton.addEventListener("click", () => {
        filterActive = !filterActive;
        filterResults(filterActive);
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

// Export Button
function exportVisibleToMarkdown() {
    const root = document.getElementById("results");
    const overallTitle = document.getElementById("achiev_title").innerText.trim();

    let md = "# Achievement Progress\n\n";
    if (overallTitle) {
        md += `## ${overallTitle}\n\n`;
    }

    function processList(ul, depth = 0) {
        const items = ul.querySelectorAll(":scope > li.list-group-item:not(.hidden-done)");

        items.forEach(item => {
            const indent = "  ".repeat(depth);

            // Get main label
            const textNodes = [...item.childNodes].filter(n => n.nodeType === Node.TEXT_NODE);
            const name = textNodes.map(n => n.textContent.trim()).join(" ").trim();

            // Wowhead link
            const linkEl = item.querySelector(".achiev-link");
            const link = linkEl ? linkEl.href : "";

            // Description
            const descEl = item.querySelector(".achiev-desc");
            const desc = descEl ? descEl.textContent.trim() : "";

            // Progress like "3/10"
            const progressText = item.textContent.match(/\d+\/\d+/);
            const progress = progressText ? ` (${progressText[0]})` : "";

            // Done or not
            const isDone = item.classList.contains("list-group-item-success");
            const checkbox = isDone ? "[x]" : "[ ]";

            md += `${indent}- ${checkbox} ${name}${progress}`;
            if (link) md += ` [Wowhead](${link})`;
            if (desc) md += ` — ${desc}`;
            md += "\n";

            // Look for siblings (children)
            const nextEl = item.nextElementSibling;
            if (nextEl && nextEl.tagName === "UL" && nextEl.classList.contains("collapse")) {
                processList(nextEl, depth + 1);
            }
        });
    }

    // Kick off recursion
    const topLevelLists = root.querySelectorAll("ul.list-group");
    topLevelLists.forEach(ul => processList(ul, 0));

    // Copy to clipboard
    navigator.clipboard.writeText(md).then(() => {
        alert("Markdown checklist copied to clipboard!");
    }).catch(err => {
        console.error("Clipboard copy failed:", err);
        const blob = new Blob([md], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "achievements.md";
        a.click();
        URL.revokeObjectURL(url);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    toggleForm();
    toggleCompleted();
    document.getElementById('results').addEventListener('click', toggleCollapse);
    document.getElementById("exportButton").addEventListener("click", exportVisibleToMarkdown);
});