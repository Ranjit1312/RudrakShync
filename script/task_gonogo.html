<!DOCTYPE html>
<html>
<head>
  <title>Go/No-Go Reaction Test</title>
</head>
<body style="text-align:center; font-family:sans-serif;">

  <h2>Go/No-Go Task</h2>
  <p>Press the <strong>SPACEBAR</strong> when the screen turns <span style="color:green;">green</span>. <br>
  Do <strong>NOT press</strong> when it turns <span style="color:red;">red</span>.</p>

  <div id="testBox" style="width:200px; height:200px; margin:auto; background-color:gray; margin-top:30px;"></div>
  <div style="margin-top:20px;" id="results"></div>

  <script>
    let trials = 20;
    let trialCount = 0;
    let goColor = "green";
    let noGoColor = "red";
    let waitTime = 1000;
    let maxWait = 2000;
    let startTime = 0;
    let listening = false;

    let data = {
      reactionTimes: [],
      falseAlarms: 0,
      misses: 0,
      correctHits: 0,
      totalGo: 0,
      totalNoGo: 0
    };

    function nextTrial() {
      trialCount++;
      listening = false;
      let isGo = Math.random() > 0.4; // 60% go, 40% no-go
      let color = isGo ? goColor : noGoColor;
      if (isGo) data.totalGo++; else data.totalNoGo++;

      document.getElementById("testBox").style.backgroundColor = "gray";

      setTimeout(() => {
        document.getElementById("testBox").style.backgroundColor = color;
        startTime = new Date().getTime();
        listening = true;

        // If no response in 1.5s on GO trial, count as miss
        if (isGo) {
          setTimeout(() => {
            if (listening) {
              data.misses++;
              listening = false;
            }
            if (trialCount < trials) nextTrial(); else finish();
          }, 1500);
        } else {
          // On No-Go, just wait 1.5s
          setTimeout(() => {
            listening = false;
            if (trialCount < trials) nextTrial(); else finish();
          }, 1500);
        }

      }, Math.random() * maxWait + waitTime);
    }

    document.body.onkeyup = function(e) {
      if (e.code === "Space" && listening) {
        let rt = new Date().getTime() - startTime;
        let boxColor = document.getElementById("testBox").style.backgroundColor;
        if (boxColor === goColor) {
          data.reactionTimes.push(rt);
          data.correctHits++;
        } else {
          data.falseAlarms++;
        }
        listening = false;
      }
    };

    function finish() {
      let avgRT = Math.round(data.reactionTimes.reduce((a, b) => a + b, 0) / (data.reactionTimes.length || 1));
      let html = `
        <h3>Results</h3>
        <p><strong>Avg Reaction Time:</strong> ${avgRT} ms</p>
        <p><strong>Correct Hits:</strong> ${data.correctHits} / ${data.totalGo}</p>
        <p><strong>False Alarms:</strong> ${data.falseAlarms} / ${data.totalNoGo}</p>
        <p><strong>Misses:</strong> ${data.misses}</p>
      `;
      document.getElementById("results").innerHTML = html;

      // Optionally send to parent app
      window.parent.postMessage({ type: "gonogo_results", data }, "*");
    }

    nextTrial();
  </script>

</body>
</html>
