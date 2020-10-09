$(document).ready(function()
{

    /**
     * Handle the Save Setup - Site Information.
     * This will pass all the site information to the
     * backend to save to the project.
     */
    $('#modalSetupSiteInfoBtnSave').click(function(event) {
        console.log("Save Setup Site Information");

        // grab values
        input_site_name = $('#modalSetupSiteInfoSiteName').val();
        input_station_number = $("#modalSetupSiteInfoStationNumber").val();
        input_location = $("#modalSetupSiteInfoLocation").val();
        input_party = $("#modalSetupSiteInfoParty").val();
        input_boat = $("#modalSetupSiteInfoBoat").val();
        input_measurement_num = $("#modalSetupSiteInfoMeasurementNum").val();
        input_comments = $("#modalSetupSiteInfoComments").val();
        console.log(input_site_name, input_station_number, input_location, input_party, input_boat, input_measurement_num, input_comments);

        $.ajax({
            type: "POST",
            url: "/setup_site_info",
            data: {
                    'site_name' : input_site_name,
                    'station_number' : input_station_number,
                    'location': input_location,
                    'party': input_party,
                    'boat': input_boat,
                    'measurement_num': input_measurement_num,
                    'comments': input_comments,
                    },
            success: function (response) {
                console.log(response)  // display the returned data in the console.

                // Check for any errors when trying to connect
                if(response.is_setup_site_info_save_error)
                {
                    $('#errorSetupSiteInfoAlert').text(response.setup_site_info_error_status[0]).show();
                    $('#successSetupSiteInfoAlert').hide()
                }
            }
        });

        // Prevent it being called twice
        event.preventDefault();

    });


});