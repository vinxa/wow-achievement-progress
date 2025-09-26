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
    const form = document.getElementById('achForm');
    const toggle = document.getElementById('formToggle');

    const params = new URLSearchParams(new FormData(e.target));
    document.getElementById('loading').style.display = 'block';
    document.getElementById("generateButton").disabled = true;
    document.getElementById("achiev_title").innerText = "";
    document.getElementById("filterButton").classList.add("d-none");
    document.getElementById("exportButton").classList.add("d-none");
    const results = document.getElementById('results');
    results.innerHTML = '';
    fetch('/achievement?' + params.toString())
        .then(resp => resp.json())
        .then(data => {
            if (data.error) {
                results.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                form.classList.remove('collapsed');
                toggle.classList.add('d-none');
                document.getElementById('loading').style.display = 'none';
                document.getElementById("generateButton").disabled = false;
                return;
            }
            results.innerHTML = '';

            const characterServerSlug = `${data.character}-${data.server}`.replace(/[^A-Za-z0-9-]/g, '');

            results.appendChild(renderSteps(data.steps, 0, false, characterServerSlug));
            // Sort out visibility
            document.getElementById('loading').style.display = 'none';
            document.getElementById('title').classList.add('collapsed');
            document.getElementById("generateButton").disabled = false;
            document.getElementById("filterButton").classList.remove("d-none");
            document.getElementById("exportButton").classList.remove("d-none");

            // Update results title
            const titleEl = document.getElementById("achiev_title");
            const isDone = data.parent.done;
            const wowheadUrl = `https://www.wowhead.com/achievement=${data.parent.id}`;

            const checkbox = isDone ? "✅" : "";
            titleEl.innerHTML = `
            ${checkbox} <a href="${wowheadUrl}" target="_blank" rel="noopener noreferrer">
                ${data.parent.name}
            </a> (${data.character}-${data.server_name})`; 

            if (isDone) {
                titleEl.classList.add('completed');
            } else {
                titleEl.classList.remove('completed');
            }

            // refresh links for Wowhead Power addon if it exists
            if (typeof $WowheadPower !== "undefined") {
                $WowheadPower.refreshLinks();
            }

            form.classList.add('collapsed');
            toggle.classList.remove('d-none');
            toggle.innerText = "▼ Show Form";
            filterResults(filterActive);
        });
}

document.getElementById('achForm').addEventListener('submit', generateAchievementProgress);

