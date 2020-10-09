function init_amp_plot( ){
    var trace1 = {
      x: [],
      y: [],
      type: 'scatter',
      name: 'Amplitude (dB)'
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

    var livePlotDiv = document.getElementById("amp-plot");
    if(livePlotDiv)
    {
        Plotly.newPlot('amp-plot', data, layout, additional_param);
    }
};

/**
 * Receive the plot data from the websocket.
 * Update the plot with the new information.
*/
function update_amp_plot( beam0, beam1, beam2, beam3, beamVert, binDepthList, is_upward ){
    //console.log(x)
    //#console.log(y)

    var beam0 = {
      x: beam0,
      y: binDepthList,
      type: 'scatter',
      name: "Beam 0"
    };

    var beam1 = {
      x: beam1,
      y: binDepthList,
      type: 'scatter',
      name: "Beam 1"
    };

    var beam2 = {
      x: beam2,
      y: binDepthList,
      type: 'scatter',
      name: "Beam 2"
    }

    var beam3 = {
      x: beam3,
      y: binDepthList,
      type: 'scatter',
      name: "Beam 3"
    };

    var beamVert = {
      x: beamVert,
      y: binDepthList,
      type: 'scatter',
      name: "Vert Beam"
    };

    if(is_upward)
    {
        var layout = {
            showlegend: false,               // Show the line legend
            uirevision:'true',              // Keep the UI zoom levels on update
            autosize: true,                 // Maximum size
            width: 200,
            legend: {"orientation": "h"},
            margin: {
                l: 0,
                r: 0,
                b: 0,
                t: 0,
            },
            yaxis: {
                automargin: true,
                title: {
                    text: "Depth (m)",
                    font: {
                        size: 10,
                    },
                },
            },
            xaxis: {
                automargin: true,
                title: {
                    text: "SNR (db)",
                    font: {
                        size: 10,
                    },
                },
            },
        };
    }
    else
    {
            var layout = {
            showlegend: false,               // Show the line legend
            uirevision:'true',              // Keep the UI zoom levels on update
            autosize: true,                 // Maximum size
            width: 200,
            legend: {"orientation": "h"},
            yaxis: {
                autorange: 'reversed',
                automargin: true,
                title: {
                    text: "Depth (m)",
                    font: {
                        size: 10,
                    },
                },
            },
            xaxis: {
                automargin: true,
                title: {
                    text: "SNR (db)",
                    font: {
                        size: 10,
                    },
                },
            },
            margin: {
                l: 0,
                r: 0,
                b: 0,
                t: 0,
            },
        };
    }

    var additional_param = {
        responsive: true,               // Adjust the plot size with the window size
        displaylogo: false              // Remove plotly button
    };

    var data = [beam0, beam1, beam2, beam3, beamVert];

    var livePlotDiv = document.getElementById("amp-plot");
    if(livePlotDiv)
    {
        Plotly.react('amp-plot', data, layout);
    }
};
