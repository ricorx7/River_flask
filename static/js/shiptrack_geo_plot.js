function init_shiptrack_geo_plot( ){
    var trace1 = {
      x: [],
      y: [],
      type: 'scattergeo',
      name: 'Ship Track Geo'
    };

    var data = [trace1];

    var layout = {
        showlegend: true,               // Show the line legend
        autosize: true,
        uirevision: 'true',              // Keep the UI zoom levels on update
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


    };

    var additional_param = {
        responsive: true,               // Adjust the plot size with the window size
        displaylogo: false,              // Remove plotly button
        //mapboxAccessToken: "pk.eyJ1Ijoicm93ZXRlY2hpbmMiLCJhIjoiY2tlMmh5ZDA3MDlkcjJ1dWw1Z2E0eGUyNCJ9.CESo0o0akLXS_a8u9-6B_A",
    };

    console.log("Look for ShipTrack Geo");
    var shiptrackPlotDiv = document.getElementById("shiptrack-geo-plot");
    if(shiptrackPlotDiv)
    {
        console.log("Create ShipTrack Geo");
        Plotly.newPlot('shiptrack-geo-plot', data, layout, additional_param);
    }
};

/**
 * Receive the plot data from the websocket.
 * Update the plot with the new information.
*/
function update_shiptrack_geo_plot( lat, lon, min_lat, min_lon, max_lat, max_lon, mid_lat, mid_lon, wv_lat, wv_lon, wv_desc){

    //console.log(lat)
    //console.log(lon)
    //console.log(min_lat)
    //console.log(min_lon)
    //console.log(max_lat)
    //console.log(max_lon)

    var st = {
      lat: lat,
      lon: lon,
      type: 'scattergeo',
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
      lat: wv_lat,
      lon: wv_lon,
      type: 'scattergeo',
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
        uirevision: 'true',              // Keep the UI zoom levels on update
        margin: {
            l: 0,
            r: 0,
            b: 0,
            t: 0
        },
        yaxis: {
            automargin: true,
            autorange: true,
         },
        xaxis: {
            automargin: true,
            autorange: true,
        },
        geo: {
            scope: 'north america',
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
            //showland: true,
            //landcolor: "rgb(212, 212, 212)",
            //countrycolor: "rgb(212, 212, 212)",
            //countrywidth: 1.5,
            //subunitcolor: '#d3d3d3'
            showland: true,
            landcolor: "rgb(212, 212, 212)",
            subunitcolor: "rgb(255, 255, 255)",
            countrycolor: "rgb(255, 255, 255)",
        }


    };

    var data = [st, wv];


    var shiptrackPlotDiv = document.getElementById("shiptrack-geo-plot");
    if(shiptrackPlotDiv)
    {
        Plotly.react('shiptrack-geo-plot', data, layout);
    }
};
