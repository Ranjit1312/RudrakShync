<!DOCTYPE html>
<html>
<head>
  <title>2-Back Task</title>
</head>
<body style="text-align:center; font-family:sans-serif;">

  <h2>2-Back Memory Test</h2>
  <p>Press <strong>SPACEBAR</strong> if the current letter matches the one 2 steps back.</p>
  <div id="letter" style="font-size:100px; margin:40px;"></div>
  <div id="results"></div>

  <script>
    const totalTrials = 25;
    let sequence = [];
    let currentIndex = 0;
    let hits = 0, falseAlarms = 0, misses = 0;
    let responses = [];

    function generateSequence() {
      const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
      for (let i = 0; i < totalTrials; i++) {
        if (i >= 2 && Math.random() > 0.7) {
          sequence.push(sequence[i - 2]);
        } else {
          sequence.push(letters[Math.floor(Math.random() * letters.length)]);
        }
      }
    }

    function showNextLetter() {
      if (currentIndex >= totalTrials) return showResults();

      document.getElementById("letter").textContent = sequence[currentIndex];
      let expected = (currentIndex >= 2 && sequence[currentIndex] === sequence[currentIndex - 2]);

      let responded = false;
      let trialStart = Date.now();

      document.body.onkeyup = function (e) {
        if (e.code === "Space" && !responded) {
          responded = true;
          let rt = Date.now() - trialStart;
          if (expected) {
            hits++;
          } else {
            falseAlarms++;
          }
          responses.push({ index: currentIndex, rt, correct: expected });
        }
      };

      setTimeout(() => {
        if (!responded) {
          if (expected) misses++;
          responses.push({ index: currentIndex, rt: null, correct: !expected });
        }
        currentIndex++;
        showNextLetter();
      }, 1500);
    }

    function showResults() {
      document.getElementById("letter").textContent = "";
      let html = `
        <h3>Results</h3>
        <p><strong>Hits:</strong> ${hits}</p>
        <p><strong>False Alarms:</strong> ${falseAlarms}</p>
        <p><strong>Misses:</strong> ${misses}</p>
      `;
      document.getElementById("results").innerHTML = html;

      // Post back to parent app
      window.parent.postMessage({ type: "twoback_results", data: { hits, falseAlarms, misses, responses } }, "*");
    }

    generateSequence();
    showNextLetter();
  </script>

</body>
</html>
