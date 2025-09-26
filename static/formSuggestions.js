const suggestedAchievements = [
    { "id": 19458, "name": "A World Awoken (Dragonflight)" },
    { "id": 20501, "name": "Back from the Beyond (Shadowlands)" },
    { "id": 40953, "name": "A Farewell to Arms (Battle for Azeroth)" },
]

/**
 * Achievement id dropdown - select from achievement list, or type a custom id.
 * Sets up event listener for dropdown to focus search box when opened.
 */
function setupFormSuggestions() {
    const achieve_select = $("#ach_id");
    achieve_select.select2({
        theme: "bootstrap4",
        placeholder: "Select or type an achievement id",
        allowClear: true,
        tags: true,
        data: suggestedAchievements.map(ach => ({
            id: ach.id,
            text: `${ach.id} - ${ach.name}`
        })),
        createTag: function (params) {
            const term = $.trim(params.term);
            // Only allow numeric custom id
            if (/^\d+$/.test(term)) {
                $('#suggestions').addClass('d-none');
                $('#achiev_label').removeClass('mb-0');
                return { id: term, text: `${term}` };
            }
            $('#suggestions').removeClass('d-none');
            $('#achiev_label').addClass('mb-0');
            return null;
        }
    });

    achieve_select.on('select2:open', function () {
        setTimeout(() => {
            let searchBox = document.querySelector('.select2-container--open .select2-search__field');
            if (searchBox) {
                searchBox.focus();
            }
        }, 0);
    });

    achieve_select.on('select2:select', function () {
        $('#suggestions').addClass('d-none');
        $('#achiev_label').removeClass('mb-0');
    });
}

$(document).ready(function () {
    setupFormSuggestions();
});
