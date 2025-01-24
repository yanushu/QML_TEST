from flask import Flask, request, jsonify
import pennylane as qml
from pennylane import numpy as np  # Используем numpy из PennyLane
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)

# Пример классической модели машинного обучения
def train_classical_model(X, y):
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

# Пример квантовой схемы для оценки рисков
def quantum_circuit(inputs, weights, num_qubits):
    qml.templates.AngleEmbedding(inputs, wires=range(num_qubits))
    qml.templates.BasicEntanglerLayers(weights, wires=range(num_qubits))
    return qml.expval(qml.PauliZ(0))

# Функция для квантового машинного обучения
def train_quantum_model(X, y, num_qubits):
    dev = qml.device("default.qubit", wires=num_qubits)
    qnode = qml.QNode(quantum_circuit, dev, interface="autograd")

    # Инициализация весов
    weights = 0.01 * np.random.randn(1, num_qubits, requires_grad=True)  # Используем numpy из PennyLane

    # Оптимизация (здесь используется упрощенный подход)
    opt = qml.GradientDescentOptimizer(stepsize=0.1)
    for _ in range(100):
        # Вычисляем градиенты и обновляем веса
        weights = opt.step(lambda w: qnode(X, w, num_qubits), weights)

    return weights

# Обработка POST-запроса
@app.route('/assess_risk', methods=['POST'])
def assess_risk():
    data = request.json

    # Входные данные
    financial_data = np.array(data['financial_data'])  # Финансовые показатели
    qualitative_data = np.array(data['qualitative_data'])  # Качественные показатели
    num_qubits = data['num_qubits']  # Количество кубитов

    # Объединение данных
    X = np.concatenate([financial_data, qualitative_data])

    # Проверка на соответствие количества входных данных и кубитов
    if len(X) > num_qubits:
        return jsonify({
            "error": f"Количество входных данных ({len(X)}) превышает количество кубитов ({num_qubits})."
        }), 400

    X = X.reshape(1, -1)
    y = np.array([1])  # Пример метки (1 - хорошее состояние, 0 - плохое)

    # Нормализация данных
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Обучение классической модели
    classical_model = train_classical_model(X_scaled, y)

    # Обучение квантовой модели
    quantum_weights = train_quantum_model(X_scaled, y, num_qubits)

    # Предсказание
    classical_pred = classical_model.predict(X_scaled)
    quantum_pred = quantum_circuit(X_scaled, quantum_weights, num_qubits)

    # Вычисляем числовое значение quantum_pred
    dev = qml.device("default.qubit", wires=num_qubits)
    quantum_pred_value = qml.QNode(quantum_circuit, dev)(X_scaled, quantum_weights, num_qubits)

    # Комбинирование результатов
    final_score = (classical_pred[0] + quantum_pred_value) / 2

    # Оценка состояния
    if final_score >= 0.7:
        status = "Хорошее"
    elif 0.4 <= final_score < 0.7:
        status = "Среднее"
    else:
        status = "Плохое"

    # Возврат результата
    return jsonify({
        "financial_status": status,
        "classical_prediction": int(classical_pred[0]),
        "quantum_prediction": float(quantum_pred_value),
        "final_score": float(final_score)
    })

if __name__ == '__main__':
    # Запуск сервера на localhost:5000
    app.run(debug=True)