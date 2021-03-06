
$(document).ready(function()
{
    // ------------------------------ WEBSOCKET -----------------------------------------------//

    // Use a "/test" namespace.
    // An application can open a connection on multiple namespaces, and
    // Socket.IO will multiplex all those connections on a single
    // physical channel. If you don't care about multiple channels, you
    // can set the namespace to an empty string.
    namespace = '/rti';

    // Connect to the Socket.IO server.
    // The connection URL has the following format, relative to the current page:
    //     http[s]://<domain>:<port>[/<namespace>]
    var socket = io(namespace);

    // Event handler for new connections.
    // The callback function is invoked when a connection with the
    // server is established.
    socket.on('connect', function() {
        init_volt_plot();
        init_heatmap_plot();
        init_shiptrack_plot();
        init_shiptrack_mapbox_plot();
        //init_shiptrack_geo_plot();
        init_depth_plot();
        init_amp_plot();
    });

    // Event handler for new connections.
    // The callback function is invoked when a connection with the
    // server is established.
    socket.on('disconnect', function() {

    });


    // Event handler for server sent data.
    // The callback function is invoked whenever the server emits data
    // to the client. The data is then displayed in the "Received"
    // section of the page.
    socket.on('status_report', function(msg, cb) {
        //$('#log').append('<br>' + $('<div/>').text('Received #' + msg.count + ': ' + msg.data).html());
        //if (cb)
        //    cb();
    });

    /**
     * Update the serial communication console to see the latest serial
     * communication
     */
    socket.on('serial_comm', function(msg, cb) {
        //console.log("serial_comm");
        // Update the console
        $("textarea#txtSerialOutput").html(msg.data);
    });

    /**
     * Receiver the latest Ensemble information
     */
    socket.on('adcp_ens', function(msg, cb) {
        // Update the ensemble number
        $("#adcpEnsNumLabel").text(msg.adcp_ens_num);
        $("#adcpEnsNumStatusLabel").text(msg.adcp_ens_num);

        // Tabular data
        $("#adcpEnsNumSysTabularLabel").text(msg.adcp_ens_num);
        $("#ensTimeSysTabularLabel").text(msg.ens_time);
        $("#transectDurationSysTabularLabel").text(msg.transect_duration);
        $("#voltageSysTabularLabel").text(msg.voltage);
        $("#headingSysTabularLabel").text(msg.heading);
        $("#pitchSysTabularLabel").text(msg.pitch);
        $("#rollSysTabularLabel").text(msg.roll);
        $("#waterTempSysTabularLabel").text(msg.water_temp);
    });

    /**
     * Create the plots.  This will get the initial date and time for the
     * plots.
     */
    socket.on('init_plots', function (msg) {
        // Function defined in volt_plot.js and heatmap_plot.js
        console.log("Init Plots");
        init_volt_plot();
        init_heatmap_plot();
        init_shiptrack_plot();
        init_shiptrack_mapbox_plot();
        //init_shiptrack_geo_plot();
        init_depth_plot();
        init_amp_plot();
    });

    /**
     * Update the volt plot with the latest data.
     */
    socket.on('update_volt_plot', function (msg) {
        // Function defined in volt_plot.js
        update_volt_plot( msg.x, msg.y );
    });

    /**
     * Update the amplitude plot with the latest data.
     */
    socket.on('update_amp_plot', function (msg) {
        // Function defined in amp_plot.js
        update_amp_plot( msg.beam0,
                         msg.beam1,
                         msg.beam2,
                         msg.beam3,
                         msg.beamVert,
                         msg.binDepth,
                         msg.is_upward);
    });

    /**
     * Update the Ship Track plot with the latest data.
     */
    socket.on('update_shiptrack_plot', function (msg) {
        // Function defined in shiptrack_plot.js
        update_shiptrack_plot( msg.lat,
                               msg.lon,
                               msg.min_lat,
                               msg.min_lon,
                               msg.max_lat,
                               msg.max_lon,
                               msg.mid_lat,
                               msg.mid_lon,
                               msg.wv_lat,
                               msg.wv_lon,
                               msg.wv_desc);

        // Function defined in shiptrack_mapbox_plot.js
        update_shiptrack_mapbox_plot( msg.lat,
                               msg.lon,
                               msg.min_lat,
                               msg.min_lon,
                               msg.max_lat,
                               msg.max_lon,
                               msg.mid_lat,
                               msg.mid_lon,
                               msg.wv_lat,
                               msg.wv_lon,
                               msg.wv_desc);

    });

    /**
     * Update the heatmap plot with the latest data.
     */
    socket.on('update_heatmap_plot', function (msg) {
        // Function defined in heatmap_plot.js
        update_heatmap_plot( msg.hm_x,
                             msg.hm_y,
                             msg.hm_z,
                             msg.bt_x,
                             msg.bt_y,
                             msg.bottom_x,
                             msg.bottom_y,
                             msg.is_upward,
                             msg.colorscale,
                             msg.min_z,
                             msg.max_z);

        update_depth_plot( msg.bt_x,
                            msg.bt_y,
                            msg.is_upward);
    });

});
