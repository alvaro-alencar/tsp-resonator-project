# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import resonator_tsp as rt

app = Flask(__name__)
CORS(app) 

@app.route('/solve', methods=['POST'])
def solve_tsp():
    """
    Endpoint da API para resolver uma instância do TSP.
    Recebe as coordenadas e parâmetros, e retorna a solução completa,
    incluindo a rota final para visualização.
    """
    try:
        data = request.get_json()
        coords = data.get('coords')
        params = data.get('params')
        
        N = int(params.get('N', 10))
        A = float(params.get('A', 0.003))
        s = float(params.get('shift', 0.33))
        ils_iter = int(params.get('ils_iter', 100))

        if not coords or not isinstance(coords, list):
            return jsonify({"error": "Coordenadas ('coords') inválidas ou ausentes."}), 400

        dist_matrix = rt.compute_distance_matrix(coords)
        
        # Agora capturamos a rota final retornada pela função
        initial_cost, final_cost, final_route = rt.run_trial(
            coords=coords,
            dist_matrix=dist_matrix,
            N=N,
            amplitude=A,
            shift=s,
            ils_iterations=ils_iter
        )
        
        return jsonify({
            "initial_cost": initial_cost,
            "final_cost": final_cost,
            "final_route": final_route, # Enviando a rota para o frontend!
            "message": "Solução encontrada com sucesso!"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Reinicie o servidor se ele estiver rodando (CTRL+C e depois 'python app.py')
    app.run(debug=True, port=5000)