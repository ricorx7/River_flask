function init_heatmap_plot( ){
    var heatmap = {
      x: [],
      y: [],
      z: [],
      type: 'heatmap',
      colorscale: 'Cividis',
      name: 'Water Velocity'
    };

    var bt_range = {
      x: [],
      y: [],
      type: 'scatter',
      name: 'Range'
    };

    var data = [heatmap, bt_range];

    layout = {
        showlegend: true,               // Show the line legend
        uirevision:'true',              // Keep the UI zoom levels on update
    }

    additional_param = {
        responsive: true,               // Adjust the plot size with the window size
        displaylogo: false              // Remove plotly button
    }

    var livePlotDiv = document.getElementById("heatmap-plot");
    if(livePlotDiv)
    {
        Plotly.newPlot('heatmap-plot', data, layout, additional_param);
    }
};

/**
 * Receive the plot data from the websocket.
 * Update the plot with the new information.
*/
function update_heatmap_plot( hm_x, hm_y, hm_z, bt_x, bt_y  ){
    //console.log(x)
    //#console.log(y)

    var heatmap = {
      x: hm_x,
      y: hm_y,
      z: hm_z,
      type: 'heatmap',
      colorscale: 'Cividis',
      name: 'Water Velocity'
    };

    var bt_range = {
      x: bt_x,
      y: bt_y,
      type: 'scatter',
      name: 'Range'
    };

    layout = {
        showlegend: true,               // Show the line legend
        uirevision:'true',              // Keep the UI zoom levels on update
    }

    additional_param = {
        responsive: true,               // Adjust the plot size with the window size
        displaylogo: false              // Remove plotly button
    }

    var data = [heatmap, bt_range];

    var livePlotDiv = document.getElementById("heatmap-plot");
    if(livePlotDiv)
    {
        Plotly.react('heatmap-plot', data, layout);
    }
};
