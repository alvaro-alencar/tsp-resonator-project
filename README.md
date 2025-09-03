# TSP Resonator Project

Este repositório traz uma implementação completa do *SAT Resonator* aplicada ao problema do caixeiro viajante (TSP) com uma interface web responsiva e um back‑end em Python para experimentos mais avançados.

## Estrutura do projeto

```
├── frontend/
│   ├── index.html       # Página principal com a interface gráfica
│   ├── scripts.js       # Lógica em JavaScript para leitura do TSPLIB e execução do resonator
│   └── style.css        # Folha de estilos responsiva
├── backend/
│   ├── resonator_tsp.py # Implementação em Python do algoritmo ressonante
│   └── README.md        # Documentação do módulo Python
├── berlin52.tsp         # Instância TSPLIB utilizada como exemplo
└── README.md            # (este arquivo) Visão geral do projeto
```

### Front‑end

A pasta **frontend** contém uma aplicação web estática que permite:

* Carregar um arquivo `.tsp` de instância do TSP (no formato TSPLIB).
* Definir parâmetros de amplitude (`A`), fase (`s`) e número de harmônicas (`N`).
* Executar o *SAT Resonator* diretamente no navegador (em JavaScript), obtendo a rota inicial, aplicando 2‑Opt e exibindo:
  - Um gráfico dispersão de **tempo vs. custo** para cada execução.
  - Um mapa interativo da rota encontrada em um `<canvas>`.
  - Uma tabela com os parâmetros utilizados, o custo final e o tempo de execução.

O design utiliza flexbox para se adaptar a diferentes tamanhos de tela, cores suaves e tipografia agradável para uma experiência de uso moderna e responsiva.

### Back‑end

A pasta **backend** traz um módulo Python que implementa o mesmo algoritmo. Ele é útil para testes automatizados, varreduras de parâmetros e experimentos offline que podem ser executados diretamente via terminal. Consulte `backend/README.md` para instruções detalhadas de uso.

### Como executar

1. **Abrir a interface web:**
   Abra `frontend/index.html` no seu navegador preferido. Não há dependências de servidor; tudo roda localmente no navegador.

2. **Rodar experimentos em Python:**
   Instale Python 3 e execute:
   ```bash
   cd backend
   python3 resonator_tsp.py ../berlin52.tsp --N 7 8 9 10 --A 0.003 0.005 --shift 0.25 0.29 --seeds 3 --two_opt_iter 1000 --output resultados.csv
   ```

3. **Testar no VSCode:**
   Importe a pasta inteira (`tsp_resonator_project`) no VSCode. Você terá acesso tanto ao front‑end quanto ao back‑end, podendo modificar e experimentar à vontade.

## Licença

O projeto é fornecido sob a licença MIT; consulte o cabeçalho de `backend/resonator_tsp.py` para mais detalhes.