let hostname = "";
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
        step: function (state, circle) {
            circle.path.setAttribute('stroke', '#333');
            circle.path.setAttribute('stroke-width', 4);

            if (circle.text == null) {
                circle.setText("?");
            }
        }

    });
    bar.text.style.fontSize = '2rem';
    return bar;
}

function updateProgress(userId) {
    const http = new XMLHttpRequest();

    http.open("GET", hostname + "/api/getProgress?id=" + userId);
    http.send();

    http.onload = () => {
        let progressJson = JSON.parse(http.responseText);
        if (progressJson.current_step != "done") {
            document.getElementById("step-text").textContent = progressJson.message;
            progressBar.setText(progressJson.count.completed + "/" + progressJson.count.total);
            progressBar.animate(progressJson.count.completed / progressJson.count.total);
        } else {
            progressBar.setText('Completed!');
            progressBar.animate(1);
            document.getElementById("progress-container").classList.add("hidden");
            loadUserData(userId);
            setTimeout(function () {
                document.getElementById("ui").classList.add("visible");
            }, 1000);

            clearInterval(updateInterval);
        }
    }
}

function loadUserData(userId) {
    const http = new XMLHttpRequest();

    http.open("GET", hostname + "/api/getBasicUser?id=" + userId);
    http.send();

    http.onload = () => {
        let userDataJson = JSON.parse(http.responseText);

        console.log(userDataJson);

        if (!userDataJson.error) {
            document.getElementById("level").textContent = "Lv." + userDataJson["level"];
            document.getElementById("name").textContent = userDataJson["name"];
            document.getElementById("title").textContent = userDataJson["title"];
            document.getElementById("points").textContent = userDataJson["points"];
            document.getElementById("icon").src = "/static/assets/icon/" + userDataJson["icon"] + ".png";
            document.getElementById("color").src = "/static/assets/color/" + userDataJson["color"] + ".png";
        } else {
            setTimeout(loadUserData, 1000, userId);
        }
    }
}

function downloadDump() {
    fetch(hostname + "/api/download?id=" + userId)
        .then(resp => resp.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            // the filename you want
            a.download = 'wacca_data_'+userId+'.json';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            console.log('downloading dump!'); // or you know, something with better UX...
        })
        .catch(() => alert('oh no, dump download failed!'));
}

let progressBar = newBar("progress1");
let userId = new URLSearchParams(location.search).get("id");
let updateInterval = setInterval(updateProgress, 1000, userId);