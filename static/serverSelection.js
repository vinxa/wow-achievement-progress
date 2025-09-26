
/**
 * Loads the list of realms for the given region into the #serverSelect select.
 * @param {string} [region="us"] - The region to load realms for.
 */
async function loadRealms(region = "us") {
  const resp = await fetch(`/realms?region=${region}&t=${Date.now()}`);
  const realms = await resp.json();

  const select = $("#serverSelect");
  select.empty();

  realms.forEach(r => {
    const option = new Option(`${r.name}`,
      r.slug,
      false,
      false
    );
    select.append(option);
  });

  select.trigger("change.select2");
}

/**
 * Initializes select2 widget and loads list of realms into dropdown.
 * Sets up event listener for region select dropdown to load realm list.
 * Sets up event listener for server select dropdown to focus search box when opened.
 */
function setupServerSelection() {
    $("#serverSelect").select2({
        placeholder: "Select or type a server",
        theme: "bootstrap4",
        width: "100%"
        });

        loadRealms("us");
        $("#regionSelect").on("change", function () {
            loadRealms(this.value);
        });

        $('#serverSelect').on('select2:open', function () {
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