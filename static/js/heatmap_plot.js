function init_heatmap_plot( ){
    var trace1 = {
      x: [],
      y: [],
      type: 'scatter',
      name: 'Bottom Track Range (m)',
    };

    var data = [trace1];

    var layout = {
        showlegend: true,               // Show the line legend
        uirevision:'true',              // Keep the UI zoom levels on update
        autosize: true,                 // Maximum size
        margin: {
            l: 0,
            r: 0,
            b: 0,
            t: 0
        },
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
function update_heatmap_plot( hm_x, hm_y, hm_z, bt_x, bt_y,
                                bottom_x, bottom_y,
                                is_upward,
                                colorscale,
                                zmin, zmax){

    var bt = {
      x: bt_x,
      y: bt_y,
      type: 'scatter',
      name: "Bottom Track Range (m)",
      line: {
        color: 'rgba(255, 69, 0, 255)',
        width: 2
      },
      showlegend: false,
    };

    var bottom_line = {
      x: bottom_x,
      y: bottom_y,
      type: 'scatter',
      name: "Bottom Track Range (m)",
      fill: 'tonexty',                               // Make it a line with shade below,
      showlegend: false,
      fillcolor: 'rgba(105, 105, 105, 255)',
      line: {
        color: 'rgba(105, 105, 105, 255)',
        width: 10
      }
    };

    //console.log(hm_x)
    //console.log(hm_y)
    //console.log(hm_z)

    var hm = {
        x: hm_x,
        y: hm_y,
        z: hm_z,
        zmin: zmin,
        zmax: zmax,
        type: 'heatmap',
        name: 'Magnitude',
        colorscale: colorscale
    };


    if(is_upward)
    {
        var layout = {
            showlegend: true,               // Show the line legend
            autosize: true,
            uirevision: 'true',              // Keep the UI zoom levels on update
            yaxis: {
                automargin: true,
            },
            xaxis: {
                automargin: true,
            },
            margin: {
                l: 30,
                r: 30,
                b: 30,
                t: 30
            },
        };
    }
    else
    {
        var layout = {
            showlegend: true,               // Show the line legend
            autosize: true,
            uirevision:'true',              // Keep the UI zoom levels on update
            yaxis: {
                autorange: 'reversed',
                automargin: true,
            },
            xaxis: {
                automargin: true,
            },
            margin: {
                l: 30,
                r: 30,
                b: 30,
                t: 30,
            },
        };
    }

    var additional_param = {
        responsive: true,               // Adjust the plot size with the window size
        displaylogo: false              // Remove plotly button
    };

    var data = [hm, bt];

    var heatmapPlotDiv = document.getElementById("heatmap-plot");
    if(heatmapPlotDiv)
    {
        Plotly.react('heatmap-plot', data, layout);
    }
};
