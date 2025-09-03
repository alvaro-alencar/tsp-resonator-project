// frontend/scripts.js
(() => {
  const fileInput = document.getElementById('fileInput');
  const runButton = document.getElementById('runButton');
  const amplitudeInput = document.getElementById('amplitude');
  const shiftInput = document.getElementById('shift');
  const harmonicsInput = document.getElementById('harmonics');
  const resultsBody = document.getElementById('resultsTableBody');
  const costCanvas = document.getElementById('costChart');
  const routeCanvas = document.getElementById('routeCanvas');

  let coords = [];
  let currentFileName = '';
  const API_URL = 'http://127.0.0.1:5000/solve';

  const costCtx = costCanvas.getContext('2d');
  let chartInstance = new Chart(costCtx, {
    type: 'scatter',
    data: { datasets: [{ label: 'Tempo vs Custo', data: [], backgroundColor: '#6c5ce7' }] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { title: { display: true, text: 'Tempo (ms)' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
        y: { title: { display: true, text: 'Custo' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } }
      },
      plugins: { legend: { display: false } }
    }
  });

  fileInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (!file) return;
    currentFileName = file.name;
    const reader = new FileReader();
    reader.onload = (e) => {
      coords = parseTSP(e.target.result);
      alert(`Arquivo '${currentFileName}' carregado com ${coords.length} cidades. Pronto para resolver!`);
    };
    reader.readAsText(file);
  });

  runButton.addEventListener('click', async () => {
    if (!coords.length) {
      alert('Nenhum arquivo carregado. Selecione um arquivo .tsp primeiro.');
      return;
    }

    const params = {
      N: parseInt(harmonicsInput.value, 10),
      A: parseFloat(amplitudeInput.value),
      shift: parseFloat(shiftInput.value),
      ils_iter: 100
    };

    if (isNaN(params.A) || isNaN(params.shift) || isNaN(params.N)) {
      alert('Preencha corretamente os parâmetros numéricos.');
      return;
    }
    
    runButton.textContent = 'Calculando...';
    runButton.disabled = true;
    const startTime = performance.now();

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ coords, params }),
      });

      const result = await response.json();
      const elapsed = performance.now() - startTime;

      if (!response.ok) {
        throw new Error(result.error || 'Erro desconhecido no servidor.');
      }
      
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${currentFileName}</td>
        <td>${params.A}</td>
        <td>${params.shift}</td>
        <td>${params.N}</td>
        <td>${result.final_cost}</td>
        <td>${elapsed.toFixed(2)}</td>
      `;
      resultsBody.appendChild(row);

      chartInstance.data.datasets[0].data.push({ x: elapsed, y: result.final_cost });
      chartInstance.update();

      // Agora desenhamos a rota recebida!
      if (result.final_route) {
        drawRoute(result.final_route);
      }
      
    } catch (error) {
      console.error('Erro ao chamar a API:', error);
      alert('Não foi possível conectar ao servidor backend.\n\nDetalhes: ' + error.message);
    } finally {
        runButton.textContent = 'Rodar algoritmo';
        runButton.disabled = false;
    }
  });

  function parseTSP(text) {
    const lines = text.split(/\r?\n/);
    const coordsList = [];
    let reading = false;
    for (let line of lines) {
      const trimmed = line.trim();
      if (trimmed === 'NODE_COORD_SECTION') {
        reading = true;
        continue;
      }
      if (reading) {
        if (trimmed === '' || trimmed === 'EOF') break;
        const parts = trimmed.split(/\s+/);
        if (parts.length >= 3) {
          const x = parseFloat(parts[1]);
          const y = parseFloat(parts[2]);
          if (!isNaN(x) && !isNaN(y)) {
            coordsList.push([x, y]);
          }
        }
      }
    }
    return coordsList;
  }

  function drawRoute(route) {
    const ctx = routeCanvas.getContext('2d');
    ctx.clearRect(0, 0, routeCanvas.width, routeCanvas.height);
    if (!coords.length || !route || route.length === 0) return;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const [x, y] of coords) {
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
    }

    const pad = 20;
    const w = routeCanvas.width - 2 * pad;
    const h = routeCanvas.height - 2 * pad;
    const scale = Math.min(w / (maxX - minX || 1), h / (maxY - minY || 1));

    const toCanvas = (x, y) => {
      const canvasX = pad + (x - minX) * scale;
      const canvasY = routeCanvas.height - (pad + (y - minY) * scale);
      return [canvasX, canvasY];
    };

    ctx.strokeStyle = '#6c5ce7';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < route.length; i++) {
      const cityCoords = coords[route[i]];
      const [cx, cy] = toCanvas(cityCoords[0], cityCoords[1]);
      i === 0 ? ctx.moveTo(cx, cy) : ctx.lineTo(cx, cy);
    }
    const firstCityCoords = coords[route[0]];
    const [startX, startY] = toCanvas(firstCityCoords[0], firstCityCoords[1]);
    ctx.lineTo(startX, startY);
    ctx.stroke();

    ctx.fillStyle = '#e17055';
    ctx.strokeStyle = '#2d3436';
    for (const cityIndex of route) {
      const cityCoords = coords[cityIndex];
      const [cx, cy] = toCanvas(cityCoords[0], cityCoords[1]);
      ctx.beginPath();
      ctx.arc(cx, cy, 4, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
    }
  }
})();