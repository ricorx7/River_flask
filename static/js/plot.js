function makePlotly( x, y ){
    var trace1 = {
      x: [],
      y: [],
      type: 'scatter'
    };

    var data = [trace1];

    var livePlotDiv = document.getElementById("live-plot");
    if(livePlotDiv)
    {
        Plotly.newPlot('live-plot', data);
    }
}

function streamPlotly( x, y ){
    console.log(x)
    console.log(y)

    var trace1 = {
      x: x,
      y: y,
      type: 'scatter'
    };

    var data = [trace1];

    var livePlotDiv = document.getElementById("live-plot");
    if(livePlotDiv)
    {
        Plotly.react('live-plot', data);
    }
};
