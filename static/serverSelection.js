
/**
 * Loads the list of realms for the given region into the #serverSelect select.
 * @param {string} [region="us"] - The region to load realms for.
 * @param {string}　[savedRealm=null] - optional saved realm.
 * @param {string}　[savedServer=null] - optional saved server.
 */
async function loadRealms(region = "us", savedRealm = null, savedServer = null) {
    const resp = await fetch(`/realms?region=${region}&t=${Date.now()}`);
    const realms = await resp.json();

    const select = $("#serverSelect");
    select.empty();

    realms.forEach(r => {
        const option = new Option(`${r.name}`,
            r.name,
            false,
            false
        );
        select.append(option);
    });

    if (savedServer) {
        select.val(savedServer).trigger("change");
    }

    if (savedRealm) {
        select.val(savedRealm).trigger("change");
    }

    select.trigger("change.select2");
}

/**
 * Initializes select2 widget and loads list of realms into dropdown.
 * Sets up event listener for region select dropdown to load realm list.
 * Sets up event listener for server select dropdown to focus search box when opened.
 */
function setupServerSelection() {
    const serverSelect = $("#serverSelect");
    const regionSelect = $("#regionSelect");

    serverSelect.select2({
        placeholder: "Select or type a server",
        theme: "bootstrap4",
        width: "100%"
    });

    const savedRegion = localStorage.getItem("region") || "us";
    const savedServer = localStorage.getItem("server");
    regionSelect.val(savedRegion);
    loadRealms(savedRegion, savedServer);

    regionSelect.on("change", function () {
        loadRealms(this.value);
        localStorage.setItem("region", this.value);
    });

    serverSelect.on("change", function () {
        localStorage.setItem("server", this.value);
    });

    serverSelect.on('select2:open', function () {
        setTimeout(() => {
            let searchBox = document.querySelector('.select2-container--open .select2-search__field');
            if (searchBox) {
                searchBox.focus();
            }
        }, 0);
    });
}

$(document).ready(function () {
    setupServerSelection();
});