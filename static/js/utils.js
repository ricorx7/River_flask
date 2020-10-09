$(document).ready(function()
{
    /** Make all Popovers work for Bootstrap */
    $(function () {
      $('[data-toggle="popover"]').popover()
    })

    /** Make all Tooltips work for Bootstrap */
    $(function () {
        $('[data-toggle="tooltip"]').tooltip()
    })

});