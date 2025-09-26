let nodeCounter = 0; // ensure uniqueness if no step.id exists

/**
 * Render a list of steps with nested children
 * @param {Array} steps - an array of step objects
 * @param {Number} depth - the current depth of the tree
 * @param {Boolean} parentDone - whether the parent node is done
 * @param {String} characterServerSlug - the character-server slug for wh tooltips
 * @returns {HTMLElement} an unordered list element representing the step tree
 */
function renderSteps(steps, depth = 0, parentDone = false, characterServerSlug = "") {
    const ul = document.createElement("ul");
    ul.className = "list-group";

    steps.forEach(step => {
        const done = parentDone || step.done;
        const status = done ? "success" : "danger";
        const arrow = done ? "happyarrow" : "sadarrow";
        const classes = `list-group-item list-group-item-action list-group-item-${status} a${depth}`;

        const li = document.createElement("li");
        li.className = classes;
        if (!step.children || step.children.length === 0) li.classList.add("nodrop");

        // Unique node ID (prefer step.id if available, else fallback counter)
        const nodeId = step.id ? `i${step.id}` : `i-${nodeCounter++}`;

        const achievLink = step.id
            ? ` (<a href="https://www.wowhead.com/achievement=${step.id}" target="_blank" rel="noopener noreferrer" class="achiev-link" data-wowhead="who=${characterServerSlug}&amp;when=${step.time}">${step.id}</a>)`
            : "";
        const desc = step.description
            ? ` <span class="achiev-desc">${step.description}</span>`
            : "";

        li.innerHTML = `
      ${step.icon ? `<img src="${step.icon}" class="step-icon"/>` : ""}
      ${step.children && step.children.length > 0 ? `<i class="${arrow}"></i>` : ""}
      ${step.name || ""}
      <small class="text-muted">${achievLink}${desc}</small>
      ${step.count !== undefined ? ` ${step.count}/${step.total}` : ""}
    `;

        ul.appendChild(li);

        if (step.children && step.children.length > 0) {
            const childUl = renderSteps(step.children, depth + 1, done, characterServerSlug);
            childUl.id = nodeId;
            childUl.classList.add("collapse");
            li.setAttribute("data-target", `#${nodeId}`);

            ul.appendChild(childUl);

        }
    });

    return ul;
}

function generateAchievementProgress(e) {
    e.preventDefault();
    const params = new URLSearchParams(new FormData(e.target));
    console.log(params);
    document.getElementById('loading').style.display = 'block';
    document.getElementById("generateButton").disabled = true;
    document.getElementById("achiev_title").innerText = "";
    const results = document.getElementById('results');
    results.innerHTML = '';
    fetch('/achievement?' + params.toString())
        .then(resp => resp.json())
        .then(data => {
            if (data.error) {
                results.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                return;
            }
            results.innerHTML = '';

            const characterServerSlug = `${data.character}-${data.server}`.replace(/[^A-Za-z0-9-]/g, '');
            console.log(data);

            results.appendChild(renderSteps(data.steps, 0, false, characterServerSlug));
            document.getElementById('loading').style.display = 'none';
            document.getElementById("generateButton").disabled = false;
            document.getElementById("achiev_title").innerText = `${data.parent.name} (${data.character}-${params.get('server')})`;
            
            // refresh links for Wowhead Power addon if it exists
            if (typeof $WowheadPower !== "undefined") {
                $WowheadPower.refreshLinks();
            }
        });
}

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

document.getElementById('achForm').addEventListener('submit', generateAchievementProgress);
document.getElementById('results').addEventListener('click', toggleCollapse);