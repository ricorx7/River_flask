function init_depth_plot( ){
    var trace1 = {
      x: [],
      y: [],
      type: 'scatter',
      name: 'Depth (m)'
    };

    var data = [trace1];

    var layout = {
        title: "Depth Plot",
        showlegend: true,               // Show the line legend
        uirevision:'true',              // Keep the UI zoom levels on update
        autosize: true,                 // Maximum size
    };

    var additional_param = {
        responsive: true,               // Adjust the plot size with the window size
        displaylogo: false              // Remove plotly button
    };

    console.log("Look for Depth");
    var depthPlotDiv = document.getElementById("depth-plot");
    if(depthPlotDiv)
    {
        console.log("Create Depth");
        Plotly.newPlot('depth-plot', data, layout, additional_param);
    }
};

/**
 * Receive the plot data from the websocket.
 * Update the plot with the new information.
*/
function update_depth_plot( bt_x, bt_y, is_upward ){

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

    //console.log(bt_x)
    //console.log(bt_y)

    //console.log(hm_x)
    //console.log(hm_y)
    //console.log(hm_z)


    if(is_upward)
    {
        var layout = {
            showlegend: true,               // Show the line legend
            autosize: true,
            uirevision:'true',              // Keep the UI zoom levels on update
            yaxis: {
                autorange: 'reversed',
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

    var data = [bt];


    var depthPlotDiv = document.getElementById("depth-plot");
    if(depthPlotDiv)
    {
        Plotly.newPlot('depth-plot', data, layout);
    }
};
