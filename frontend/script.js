function newBar() {
    let bar = new ProgressBar.Circle(container, {
        color: '#aaa',
        // This has to be the same size as the maximum width to
        // prevent clipping
        strokeWidth: 4,
        trailWidth: 1,
        easing: 'easeInOut',
        duration: 1400,
        text: {
          autoStyleContainer: false
        },
      
        // Set default step function for all animate calls
        step: function(state, circle) {
            circle.path.setAttribute('stroke', '#333');
            circle.path.setAttribute('stroke-width', 4);
    
            if (circle.text == null) {
                circle.setText("?")
            }
        }
    
      });
    bar.text.style.fontFamily = '"Raleway", Helvetica, sans-serif';
    bar.text.style.fontSize = '2rem';
    return bar
}

var bests = newBar()
bests.setText('1/20')
bests.animate(1/20)