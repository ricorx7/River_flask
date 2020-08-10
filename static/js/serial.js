$(document).ready(function()
{

    /**
     * Handle the Serial port SCAN button.
     * This will reset the serial port list
     * then set the previously selected COMM port.
     */
    $('#btnScan').click(function() {
        console.log("SCAN BUTTON CLICKED");

        // grab values
        comm_port = $('#comm_port').val();
        baud_rate = $("#baud_rate").val();
        console.log(comm_port, baud_rate);

        $.ajax({
            type: "POST",
            url: "/serial_scan",
            data: $('form').serialize(), // serializes the form's elements.
            success: function (response) {
                console.log(response)  // display the returned data in the console.
                // Clear the list then Update the list of comm ports
                $("#comm_port").empty();
                response.data.port_list.forEach(function(item) {
                    //console.log(response.data.port_list[i]);
                    $("#comm_port").append(new Option(item, item));
                });

                // Reselect the original selections
                $('#comm_port').val(comm_port);
            }
        });
    });


    /**
     * Handle the Serial port SCAN button.
     * This will reset the serial port list
     * then set the previously selected COMM port.
     */
    $('#btnConnect').click(function() {
        console.log("CONNECT BUTTON CLICKED");

        // grab values
        comm_port = $('#selectComm').val();
        baud_rate = $("#selectBaud").val();
        console.log(comm_port, baud_rate);

        $.ajax({
            type: "POST",
            url: "/serial_connect",
            data: {
                    selected_port : comm_port,
                    selected_baud : baud_rate
                    },
            success: function (response) {
                console.log(response)  // display the returned data in the console.

                // Check for any errors when trying to connect
                if(response.is_serial_error)
                {
                    $('#errorSerialAlert').text(response.serial_error_status[0]).show();
                    $('#successSerialAlert').hide()
                }

                // Check if the serial port was successful at connecting
                if(response.is_serial_connected)
                {
                    $('#successSerialAlert').text(response.serial_status[0]).show();
                    $('#errorSerialAlert').hide();

                    // Disable the connect button when connected
                    $('#btnConnect').attr("disabled", true);
                }
            }
        });

        // Prevent it being called twice
        event.preventDefault();

    });

    /**
     * Handle the Serial port SCAN button.
     * This will reset the serial port list
     * then set the previously selected COMM port.
     */
    $('#btnDisconnect').click(function() {
        console.log("DISCONNECT BUTTON CLICKED");

        $.ajax({
            type: "POST",
            url: "/serial_disconnect",
            data: { },
            success: function (response) {
                console.log(response)  // display the returned data in the console.

                if(response.is_serial_error)
                {
                    $('#errorSerialAlert').text(response.serial_error_status[0]).show();
                    $('#successSerialAlert').hide()
                }
                else
                {
                    $('#successSerialAlert').text(response.serial_status[0]).show();
                    $('#errorSerialAlert').hide();
                }

                // Enable the connect button when connected
                $('#btnConnect').attr("disabled", false);
            }
        });

        // Prevent it being called twice
        event.preventDefault();
    });


    /**
     * Handle the Serial port SCAN button.
     * This will reset the serial port list
     * then set the previously selected COMM port.
     */
    $('#btnBrowseFolder').click(function() {
        console.log("Browse Folder");

        $.ajax({
            type: "POST",
            url: "/browse_folder",
            data: $('form').serialize(), // serializes the form's elements.
            success: function (response) {
                console.log(response)  // display the returned data in the console.

            }
        });

        // Prevent it being called twice
        event.preventDefault();

    });

    /**
     * Handle Sending a BREAK to the serial port.
     */
    $('#btnSerialBreak').click(function() {
        console.log("BREAK");

        $.ajax({
            type: "POST",
            url: "/serial_break",
            data: {},
            success: function (response) {
                console.log(response)  // display the returned data in the console.
                $('#adcpSerialNumLabel').text(response.serial_number);
                $('#adcpFirmwareLabel').text(response.firmware_str);
                $('#adcpModeLabel').text(response.mode);
            }
        });

        // Prevent it being called twice
        event.preventDefault();
    });

    $('#btnSerialSendCmd').click(function(event) {
        console.log("Send Command");

        $.ajax({
            type: "POST",
            url: "/serial_send_cmd",                    // API path
            data: {
                cmd : $('#inputSerialCmd').val()        // Data to pass to the FLASK api
            },
            success: function (response) {
                console.log(response)  // display the returned data in the console.
                if(response.error) {
                    $('#errorCmdAlert').text(response.error).show();
                    $('#successCmdAlert').hide();
                }
                else {
                    $('#successCmdAlert').text(response.status).show();
                    $("#successCmdAlert").fadeTo(500, 0).slideUp(500, function(){
                        $("#successCmdAlert").slideUp(500);
                    });
                    $('#errorCmdAlert').hide();

                    // Clear the text box
                    $('#inputSerialCmd').val('');
                }
            }
        });

        // Prevent it being called twice
        event.preventDefault();

    });

    /**
     * Handle Sending a Playback file selection.
     */
    $('#btnPlaybackFiles').click(function(event) {

        $.ajax({
            type: "POST",
            url: "/playback_files",
            data: { },
            success: function (response) {
                console.log(response)  // display the returned data in the console.
            }
        });

        // Prevent it being called twice
        event.preventDefault();
    });

});