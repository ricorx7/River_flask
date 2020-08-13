function init_heatmap_plot( ){
    var trace1 = {
      x: [],
      y: [],
      type: 'scatter',
      name: 'Bottom Track Range (m)'
    };

    var data = [trace1];

    var layout = {
        title: "Heatmap Plot",
        showlegend: true,               // Show the line legend
        uirevision:'true',              // Keep the UI zoom levels on update
    };

    var additional_param = {
        responsive: true,               // Adjust the plot size with the window size
        displaylogo: false              // Remove plotly button
    };

    console.log("Look for Heatmap");
    var heatmapPlotDiv = document.getElementById("heatmap-plot");
    if(heatmapPlotDiv)
    {
        console.log("Create Heatmap");
        Plotly.newPlot('heatmap-plot', data, layout, additional_param);
    }
};

/**
 * Receive the plot data from the websocket.
 * Update the plot with the new information.
*/
function update_heatmap_plot( hm_x, hm_y, hm_z, bt_x, bt_y ){

    var trace1 = {
      x: bt_x[0],
      y: bt_y[0],
      type: 'scatter',
      name: "Bottom Track Range (m)"
    };

    console.log(hm_x)
    console.log(hm_y)
    console.log(hm_z)

    var hm = {
        x: hm_x,
        y: hm_y,
        z: hm_z,
        type: 'heatmap',
        name: 'Magnitude'
    };


    var layout = {
        showlegend: true,               // Show the line legend
        uirevision:'true',              // Keep the UI zoom levels on update
    };

    var additional_param = {
        responsive: true,               // Adjust the plot size with the window size
        displaylogo: false              // Remove plotly button
    };

    var data = [hm];

    var heatmapPlotDiv = document.getElementById("heatmap-plot");
    if(heatmapPlotDiv)
    {
        Plotly.react('heatmap-plot', data, layout);
    }
};
