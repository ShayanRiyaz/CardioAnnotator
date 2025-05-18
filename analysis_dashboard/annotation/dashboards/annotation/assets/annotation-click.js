// annotation/static/annotation/js/annotation-click.js
(function(){
  console.log("🔍 annotation-click.js loaded");

  function attachClickHandler(){
    var graphDiv = document.getElementById('signal-plots');
    // wait until the graph exists and has the .on method
    if (!graphDiv || typeof graphDiv.on !== 'function') {
      console.log("…waiting for #signal-plots to be ready");
      return setTimeout(attachClickHandler, 200);
    }

    console.log("✅ Plotly graph found, attaching click handler");
    graphDiv.on('plotly_click', function(eventData){
      console.log("➡️ plotly_click:", eventData);

      var pts = eventData.points;
      if (!pts || !pts.length) return;

      var x = pts[0].x;
      console.log("   click x =", x);

      // build a new vertical line
      var newShape = {
        type: 'line',
        x0: x, x1: x,
        y0: 0,  y1: 1,
        yref: 'paper',
        line: { color: 'red', width: 1 }
      };

      // copy existing shapes and push ours
      var shapes = (graphDiv.layout.shapes || []).slice();
      shapes.push(newShape);

      // apply it
      Plotly.relayout(graphDiv, { 'layout.shapes': shapes });
    });
  }

  document.addEventListener('DOMContentLoaded', attachClickHandler);
})();