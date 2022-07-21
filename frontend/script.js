function newBar(elementId) {
  let bar = new ProgressBar.Circle(document.getElementById(elementId), {
      color: '#aaa',
      // This has to be the same size as the maximum width to
      // prevent clipping
      strokeWidth: 4,
      trailWidth: 4,
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

function checkProgress(aimeId) {
    const http = new XMLHttpRequest()

    http.open("GET", "http://localhost:8000/getProgress/?aimeId=8730272")
    http.send()

    http.onload = () => console.log(http.responseText)
}

let bests = newBar("progress1")
bests.setText('1/20')
bests.animate(1/20)

checkProgress(123123098)