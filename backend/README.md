SAT Resonator TSP
=================

Esta pasta contém uma implementação simples e auto‑contida do
heurístico **SAT Resonator** aplicada ao problema clássico do
caixeiro viajante (TSP).  O código em Python demonstra como
transformar a ideia de ressonância simbólica em um algoritmo
concreto que pode ser testado com instâncias reais.

### Arquivos principais

* **resonator_tsp.py** – Módulo principal que disponibiliza funções
  para ler instâncias da TSPLIB, calcular a rota inicial ressonante,
  refinar a rota com 2‑Opt e realizar varreduras de parâmetros.  Pode
  ser utilizado como biblioteca ou executado diretamente pela linha
  de comando.

* **README.md** – Este documento, que explica o propósito do código e
  como utilizá‑lo.

### Começando

1. **Instale Python 3.**  O script utiliza apenas a biblioteca
   padrão; não há dependências externas.

2. **Obtenha uma instância TSPLIB.**  Por exemplo, a instância
   `berlin52.tsp` pode ser encontrada no repositório TSPLIB e está
   incluída na raiz do projeto. Coloque o arquivo no mesmo
   diretório do script ou informe o caminho completo.

3. **Execute um teste simples.**  Para ver como a inicialização
   ressonante se comporta em uma única instância, rode:

   ```bash
   python3 resonator_tsp.py ../../berlin52.tsp --N 9 --A 0.003 --shift 0.29 --seeds 1 --two_opt_iter 500
   ```

   Isso computará a rota inicial ressonante para `berlin52.tsp`
   utilizando nove harmônicas (`--N 9`), amplitude de 0.003 (`--A 0.003`)
   e fase de 0.29 (`--shift 0.29`).  Executa uma semente (`--seeds 1`)
   e refina a rota com até 500 iterações de 2‑Opt (`--two_opt_iter 500`).
   O resultado é salvo em `results.csv` por padrão.

4. **Realize uma varredura de parâmetros.**  Para explorar como
   diferentes números de harmônicas, amplitudes e fases afetam a
   qualidade da solução, especifique listas para cada parâmetro.  Por exemplo:

   ```bash
   python3 resonator_tsp.py ../../berlin52.tsp \
       --N 7 8 9 10 \
       --A 0.003 0.005 0.01 \
       --shift 0.25 0.29 0.33 \
       --seeds 3 \
       --two_opt_iter 1000 \
       --output berlin52_experiments.csv
   ```

   Isto executa três sementes para cada combinação de parâmetros e
   grava os resultados em `berlin52_experiments.csv`.  O CSV conterá
   colunas com os parâmetros, semente, custo inicial, custo final e
   tempo de execução.

### Como funciona

O heurístico ressonante atribui a cada cidade um valor escalar com
base em uma série harmônica finita.  Ordenar as cidades por esses
valores gera uma rota inicial que tende a seguir uma oscilação
low‑frequency ao redor do conjunto de pontos.  O parâmetro `N`
determina quantas harmônicas estão incluídas; `amplitude` escala a
contribuição de cada termo; e `shift` introduz um deslocamento de
fase.  Valores maiores de `N` produzem oscilações mais detalhadas;
variar `amplitude` e `shift` muda o formato da onda.

Depois de obter a rota inicial, o script aplica uma busca local
2‑Opt simples para remover cruzamentos e reduzir ainda mais a
distância total.  O algoritmo 2‑Opt repete a verificação de todos
os pares de arestas e realiza a primeira troca que diminui a rota,
até que nenhuma melhora seja encontrada ou um limite de iterações
seja alcançado.

### Por que importa

Este código mostra que mesmo um heurístico ressonante muito simples
pode produzir rotas relativamente curtas com grande rapidez.  Embora
não atinja o óptimo conhecido para `berlin52` (7542 unidades),
geralmente gera tours dentro de 10–15 % do óptimo em uma fração de
segundo.  O framework experimental permite explorar sistematicamente
combinações de parâmetros, comparar desempenhos e reunir evidências
sobre a eficácia (ou limitação) da abordagem SAT Resonator.

### Licença

Este trabalho é disponibilizado sob a licença MIT; consulte o
cabeçalho de `resonator_tsp.py` para mais detalhes.