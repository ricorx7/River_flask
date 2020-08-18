function init_volt_plot( ){
    var trace1 = {
      x: [],
      y: [],
      type: 'scatter',
      name: 'voltage'
    };

    var data = [trace1];

    var layout = {
        showlegend: true,               // Show the line legend
        uirevision:'true',              // Keep the UI zoom levels on update
        autosize: true,                 // Maximum size
    };

    var additional_param = {
        responsive: true,               // Adjust the plot size with the window size
        displaylogo: false              // Remove plotly button
    };

    var livePlotDiv = document.getElementById("volt-plot");
    if(livePlotDiv)
    {
        Plotly.newPlot('volt-plot', data, layout, additional_param);
    }
};

/**
 * Receive the plot data from the websocket.
 * Update the plot with the new information.
*/
function update_volt_plot( x, y ){
    //console.log(x)
    //#console.log(y)

    var trace1 = {
      x: x,
      y: y,
      type: 'scatter',
      name: "voltage (v)"
    };

    var layout = {
        showlegend: true,               // Show the line legend
        uirevision:'true',              // Keep the UI zoom levels on update
        autosize: true,                 // Maximum size
    };

    var additional_param = {
        responsive: true,               // Adjust the plot size with the window size
        displaylogo: false              // Remove plotly button
    };

    var data = [trace1];

    var livePlotDiv = document.getElementById("volt-plot");
    if(livePlotDiv)
    {
        Plotly.react('volt-plot', data, layout);
    }
};
