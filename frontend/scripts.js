// Funções e lógica para a interface do Colapsador TSP

(() => {
  // Obtém referências aos elementos da página
  const fileInput = document.getElementById('fileInput');
  const runButton = document.getElementById('runButton');
  const amplitudeInput = document.getElementById('amplitude');
  const shiftInput = document.getElementById('shift');
  const harmonicsInput = document.getElementById('harmonics');
  const resultsBody = document.getElementById('resultsTableBody');
  const costCanvas = document.getElementById('costChart');
  const routeCanvas = document.getElementById('routeCanvas');

  let coords = [];
  let distMatrix = [];
  let currentFileName = '';

  // Inicializa gráfico de dispersão com Chart.js
  const costCtx = costCanvas.getContext('2d');
  let chartInstance = new Chart(costCtx, {
    type: 'scatter',
    data: {
      datasets: [
        {
          label: 'Tempo vs Custo',
          data: [],
          backgroundColor: '#6c5ce7',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          title: {
            display: true,
            text: 'Tempo (ms)',
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)',
          },
        },
        y: {
          title: {
            display: true,
            text: 'Custo',
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.05)',
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });

  // Lê arquivo TSPLIB quando selecionado
  fileInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (!file) {
      return;
    }
    currentFileName = file.name;
    const reader = new FileReader();
    reader.onload = function (e) {
      coords = parseTSP(e.target.result);
      distMatrix = computeDistanceMatrix(coords);
      // Feedback ao usuário
      alert(`Arquivo carregado com ${coords.length} cidades.`);
    };
    reader.readAsText(file);
  });

  // Executa o algoritmo quando o botão é clicado
  runButton.addEventListener('click', () => {
    if (!coords.length) {
      alert('Nenhum arquivo carregado. Selecione um arquivo .tsp primeiro.');
      return;
    }
    const A = parseFloat(amplitudeInput.value);
    const s = parseFloat(shiftInput.value);
    const N = parseInt(harmonicsInput.value, 10);
    if (isNaN(A) || isNaN(s) || isNaN(N)) {
      alert('Preencha corretamente os parâmetros numéricos.');
      return;
    }
    const start = performance.now();
    const initialRoute = generateResonatorRoute(coords.length, N, A, s);
    const initialCost = computeRouteCost(initialRoute, distMatrix);
    const twoOptResult = twoOpt(initialRoute, distMatrix, 2000);
    const improvedRoute = twoOptResult[0];
    const finalCost = twoOptResult[1];
    const elapsed = performance.now() - start;
    // Atualiza tabela de resultados
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${currentFileName}</td>
      <td>${A}</td>
      <td>${s}</td>
      <td>${N}</td>
      <td>${finalCost}</td>
      <td>${elapsed.toFixed(2)}</td>
    `;
    resultsBody.appendChild(row);
    // Atualiza gráfico
    chartInstance.data.datasets[0].data.push({ x: elapsed, y: finalCost });
    chartInstance.update();
    // Desenha rota no canvas
    drawRoute(improvedRoute);
  });

  // Funções utilitárias

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
        if (trimmed === '' || trimmed === 'EOF') {
          break;
        }
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

  function computeDistanceMatrix(coords) {
    const n = coords.length;
    const dist = new Array(n);
    for (let i = 0; i < n; i++) {
      dist[i] = new Array(n);
      dist[i][i] = 0;
      for (let j = i + 1; j < n; j++) {
        const dx = coords[i][0] - coords[j][0];
        const dy = coords[i][1] - coords[j][1];
        const d = Math.sqrt(dx * dx + dy * dy);
        const rounded = Math.round(d);
        dist[i][j] = rounded;
        dist[j][i] = rounded;
      }
    }
    return dist;
  }

  function computeRouteCost(route, distMatrix) {
    let total = 0;
    const n = route.length;
    for (let i = 0; i < n; i++) {
      total += distMatrix[route[i]][route[(i + 1) % n]];
    }
    return total;
  }

  function harmonicValues(n, N, amplitude, shift) {
    const values = new Array(n);
    for (let i = 0; i < n; i++) {
      const theta = 2.0 * Math.PI * ((i + shift) / n);
      let sum = 0.0;
      for (let k = 1; k <= N; k++) {
        sum += (amplitude / k) * Math.cos(k * theta);
      }
      values[i] = sum;
    }
    return values;
  }

  function generateResonatorRoute(n, N, amplitude, shift) {
    const values = harmonicValues(n, N, amplitude, shift);
    const indices = Array.from({ length: n }, (_, i) => i);
    indices.sort((a, b) => values[a] - values[b]);
    return indices;
  }

  function twoOpt(route, distMatrix, maxIterations) {
    const n = route.length;
    let bestRoute = route.slice();
    let bestCost = computeRouteCost(bestRoute, distMatrix);
    let iteration = 0;
    let improved = true;
    while (improved && iteration < maxIterations) {
      improved = false;
      for (let i = 1; i < n - 1; i++) {
        for (let j = i + 1; j < n; j++) {
          if (j - i === 1) continue;
          const a = bestRoute[i - 1], b = bestRoute[i];
          const c = bestRoute[j - 1], d = bestRoute[j % n];
          const current = distMatrix[a][b] + distMatrix[c][d];
          const proposed = distMatrix[a][c] + distMatrix[b][d];
          if (proposed < current) {
            // Reverse segmento [i, j)
            const newRoute = bestRoute.slice(0, i)
              .concat(bestRoute.slice(i, j).reverse(), bestRoute.slice(j));
            bestRoute = newRoute;
            bestCost = bestCost + (proposed - current);
            improved = true;
            break;
          }
        }
        if (improved) break;
      }
      iteration++;
    }
    return [bestRoute, bestCost];
  }

  function drawRoute(route) {
    const ctx = routeCanvas.getContext('2d');
    ctx.clearRect(0, 0, routeCanvas.width, routeCanvas.height);
    if (!coords.length || !route || route.length === 0) {
      return;
    }
    // Determine bounding box
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    for (const [x, y] of coords) {
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    }
    const pad = 20;
    const w = routeCanvas.width - 2 * pad;
    const h = routeCanvas.height - 2 * pad;
    const xScale = w / (maxX - minX || 1);
    const yScale = h / (maxY - minY || 1);
    // Helper to convert coords to canvas
    function toCanvas(x, y) {
      const cx = pad + (x - minX) * xScale;
      // invert y-axis: larger y in input becomes lower pixel
      const cy = routeCanvas.height - (pad + (y - minY) * yScale);
      return [cx, cy];
    }
    // Draw lines
    ctx.strokeStyle = '#6c5ce7';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < route.length; i++) {
      const idx = route[i];
      const [cx, cy] = toCanvas(coords[idx][0], coords[idx][1]);
      if (i === 0) ctx.moveTo(cx, cy);
      else ctx.lineTo(cx, cy);
    }
    // close the cycle
    const firstIdx = route[0];
    const [sx, sy] = toCanvas(coords[firstIdx][0], coords[firstIdx][1]);
    ctx.lineTo(sx, sy);
    ctx.stroke();
    // Draw nodes
    ctx.fillStyle = '#e17055';
    ctx.strokeStyle = '#2d3436';
    for (const idx of route) {
      const [cx, cy] = toCanvas(coords[idx][0], coords[idx][1]);
      ctx.beginPath();
      ctx.arc(cx, cy, 3, 0, 2 * Math.PI);
      ctx.fill();
      ctx.stroke();
    }
  }
})();