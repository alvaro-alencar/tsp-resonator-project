# TSP Resonator Project

Este repositório apresenta uma meta-heurística de alto desempenho para o Problema do Caixeiro Viajante (TSP), baseada no conceito original do **SAT Resonator**. A abordagem combina uma geração de rota inicial por ressonância harmônica com uma poderosa **Busca Local Iterada (ILS)** para alcançar soluções de elite, extremamente próximas ao ótimo global.

O projeto valida a tese de que a transformação de um problema combinatório em um "espaço ressonante" é uma estratégia de ponta para guiar algoritmos de busca.

## 🏆 Resultados de Desempenho

A metodologia foi validada na instância canônica `berlin52.tsp`, alcançando um resultado que a coloca entre as heurísticas de alto nível.

| Métrica | Valor |
| :--- | :--- |
| Instância | `berlin52.tsp` |
| Ótimo Conhecido | 7542 |
| **Melhor Custo (Resonator + ILS)** | **7676** |
| **Gap Percentual vs. Ótimo** | **1.78%** |
| Tempo Médio de Execução | ~400 ms |

Este resultado de elite demonstra a sinergia entre uma inicialização inteligente (ressonância) e uma busca local robusta para escapar de ótimos locais e convergir para soluções de altíssima qualidade.

## Estrutura do projeto

├── frontend/
│   ├── index.html       # Interface web para demonstração visual
│   ├── scripts.js       # Lógica da interface em JavaScript
│   └── style.css        # Folha de estilos responsiva
├── backend/
│   ├── resonator_tsp.py # Implementação em Python do algoritmo com ILS
│   └── README.md        # Documentação técnica do módulo Python
├── berlin52.tsp         # Instância TSPLIB utilizada nos benchmarks
└── README.md            # (este arquivo) Visão geral do projeto


### Como Executar

#### 1. Interface Web (Frontend)

Para uma demonstração visual do conceito de ressonância:
1.  Abra o arquivo `frontend/index.html` em qualquer navegador.
2.  Carregue um arquivo `.tsp`.
3.  Ajuste os parâmetros de ressonância e execute o algoritmo.

#### 2. Benchmarks de Precisão (Backend)

Para replicar os resultados de alto desempenho:
1.  Certifique-se de ter o Python 3 instalado.
2.  Navegue até a pasta `backend` no terminal.
3.  Execute o script com os parâmetros otimizados e a busca ILS:

```bash
# Executa o benchmark final com os melhores parâmetros e 100 iterações de ILS
python resonator_tsp.py ..\berlin52.tsp --N 10 --A 0.003 --shift 0.33 --seeds 5 --ils_iter 100
Licença
Este projeto é distribuído sob a licença MIT.git add .