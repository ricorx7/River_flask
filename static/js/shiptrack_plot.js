function init_shiptrack_plot( ){
    var trace1 = {
      x: [],
      y: [],
      type: 'scatter',
      name: 'Bottom Track Range (m)'
    };

    var data = [trace1];

    var layout = {
        showlegend: true,               // Show the line legend
        autosize: true,
        uirevision:'true',              // Keep the UI zoom levels on update
        margin: {
            l: 30,
            r: 30,
            b: 30,
            t: 30
        },
        yaxis: {
            automargin: true,
         },
        xaxis: {
            automargin: true,
        },
        /*
        geo: {
            scope: 'north america',
            resolution: 50,
            lonaxis: {
                'range': [-130, -55]
            },
            lataxis: {
                'range': [40, 70]
            },
            showrivers: true,
            rivercolor: '#fff',
            showlakes: true,
            lakecolor: '#fff',
            showland: true,
            landcolor: '#EAEAAE',
            countrycolor: '#d3d3d3',
            countrywidth: 1.5,
            subunitcolor: '#d3d3d3'
        }
        */

    };

    var additional_param = {
        responsive: true,               // Adjust the plot size with the window size
        displaylogo: false,              // Remove plotly button
        mapboxAccessToken: "pk.eyJ1Ijoicm93ZXRlY2hpbmMiLCJhIjoiY2tlMmh5ZDA3MDlkcjJ1dWw1Z2E0eGUyNCJ9.CESo0o0akLXS_a8u9-6B_A",
    };

    console.log("Look for ShipTrack");
    var shiptrackPlotDiv = document.getElementById("shiptrack-plot");
    if(shiptrackPlotDiv)
    {
        console.log("Create ShipTrack");
        Plotly.newPlot('shiptrack-plot', data, layout, additional_param);
    }
};

/**
 * Receive the plot data from the websocket.
 * Update the plot with the new information.
*/
function update_shiptrack_plot( lat, lon, min_lat, min_lon, max_lat, max_lon, wv_lat, wv_lon, wv_desc){

    //console.log(lat)
    //console.log(lon)
    //console.log(min_lat)
    //console.log(min_lon)
    //console.log(max_lat)
    //console.log(max_lon)

    var st = {
      x: lat,
      y: lon,
      type: 'scatter',
      name: "Ship Track",
      mode: 'lines',
      //marker: {
      //  size: 14
      //},
      line: {
        color: 'rgb(255, 0, 0)',
        width: 2
      },
      showlegend: false,
    };

    var wv = {
      x: wv_lat,
      y: wv_lon,
      type: 'scatter',
      name: "Water Current Vector",
      mode: 'lines',
      //marker: {
      //  size: 14
      //},
      line: {
        color: 'rgb(30, 144, 255)',
        width: 2
      },
      showlegend: false,
      hovertext: wv_desc,
    };

    var layout = {
        showlegend: true,               // Show the line legend
        autosize: true,
        uirevision: true,              // Keep the UI zoom levels on update
        margin: {
            l: 30,
            r: 30,
            b: 30,
            t: 30
        },
        yaxis: {
            automargin: true,
         },
        xaxis: {
            automargin: true,
        },
        /*
        mapbox: {
            bearing:0,
            center: {
              lat:32,
              lon:-117
            },
            pitch:0,
            zoom:8
        },
        */
        /*
        geo: {
            //scope: 'north america',
            //resolution: 50,
            lonaxis: {
                'range': [ min_lon, max_lon ],
            },
            lataxis: {
                'range': [ min_lat, max_lat ],
            },
            projection_type: 'azimuthal equal area',
            //showrivers: true,
            //rivercolor: '#fff',
            showlakes: true,
            //lakecolor: "rgb(173,216,230)",
            showland: true,
            //landcolor: "rgb(212, 212, 212)",
            //countrycolor: "rgb(212, 212, 212)",
            //countrywidth: 1.5,
            //subunitcolor: '#d3d3d3'
        }
        */

    };

    var additional_param = {
        responsive: true,               // Adjust the plot size with the window size
        displaylogo: false              // Remove plotly button
    };

    var data = [st, wv];


    var shiptrackPlotDiv = document.getElementById("shiptrack-plot");
    if(shiptrackPlotDiv)
    {
        Plotly.newPlot('shiptrack-plot', data, layout);
    }
};
