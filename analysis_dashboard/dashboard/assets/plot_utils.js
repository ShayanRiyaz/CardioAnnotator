// analysis_dashboard/dash_app/assets/plot_utils.js
window.plotUtils = {
  addCrosshair: function(figure, hoverData) {
    const x = hoverData.points[0].x;
    figure.layout.shapes = [{
      type: 'line',
      x0: x, x1: x,
      yref: 'paper', y0: 0, y1: 1,
      line: { dash: 'dot', width: 1 }
    }];
    return figure;
  }
};