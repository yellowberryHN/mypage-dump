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

function updateProgress(userId) {
  const http = new XMLHttpRequest()

  http.open("GET", "http://localhost:8000/api/getProgress?id=" + userId)
  http.send()

  http.onload = () => {
    let progressJson = JSON.parse(http.responseText)
    if(!progressJson.bests_total == undefined || !progressJson.bests_total == 0) {
      bests.setText(progressJson.bests_completed + "/" + progressJson.bests_total)
      bests.animate(progressJson.bests_completed / progressJson.bests_total)
      if(progressJson.bests_completed == progressJson.bests_total) {
        bests.setText('Completed!')
        document.getElementById("progress-container").classList.add("hidden")
        setTimeout(function(){document.getElementById("ui").classList.add("visible")}, 1000)
        
        clearInterval(updateInterval)
      }
    }
  }
}

let bests = newBar("progress1");
let userId = new URLSearchParams(location.search).get("id");
let updateInterval = setInterval(updateProgress, 1000, userId);