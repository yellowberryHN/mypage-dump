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
    if(!progressJson.songs_total == undefined || !progressJson.songs_total == 0) {
      songs.setText(progressJson.songs_completed + "/" + progressJson.songs_total)
      songs.animate(progressJson.songs_completed / progressJson.songs_total)
      if(progressJson.songs_completed == progressJson.songs_total) {
        songs.setText('Completed!')
        document.getElementById("progress-container").classList.add("hidden")
        loadUserData(userId)
        setTimeout(function(){document.getElementById("ui").classList.add("visible")}, 1000)
        
        clearInterval(updateInterval)
      }
    }
  }
}

function loadUserData(userId) {
  const http = new XMLHttpRequest()

  http.open("GET", "http://localhost:8000/api/getBasicUser?id=" + userId)
  http.send()

  http.onload = () => {
    let userDataJson = JSON.parse(http.responseText)

    console.log(userDataJson)

    if(!userDataJson.error) {
      document.getElementById("level").textContent = "Lv." + userDataJson["level"]
      document.getElementById("name").textContent = userDataJson["name"]
      document.getElementById("title").textContent = userDataJson["title"]
      document.getElementById("points").textContent = userDataJson["points"]
    }
    else {
      setTimeout(loadUserData, 1000, userId)
    }
  }


}

function downloadDump() {
  console.log("downloading dump")
}

let songs = newBar("progress1");
let userId = new URLSearchParams(location.search).get("id");
let updateInterval = setInterval(updateProgress, 1000, userId);