# 🌐 Proyecto: Nodo de Sistema Distribuido con Gossip y KVStore

## 🎯 Resumen del Proyecto

Este proyecto implementa un **Nodo de Servicio Distribuido** construido sobre **FastAPI** y **Uvicorn**. Está diseñado para operar como parte de un **clúster tolerante a fallos**, empleando el protocolo **Gossip** para el descubrimiento de *peers* y la reconciliación de datos.

El objetivo es proporcionar una plataforma robusta donde los datos clave-valor (**KVStore**) se replican con **Consistencia Eventual** y donde las tareas de cálculo (como el entrenamiento de modelos de Machine Learning) pueden ser enviadas y ejecutadas de forma distribuida.

---

## 🏗️ Arquitectura y Componentes Clave

El sistema se compone de los siguientes módulos principales, que interactúan de forma asíncrona para lograr la descentralización:

| Componente | Archivo(s) | Función Principal |
| :--- | :--- | :--- |
| **API Core** | `main.py` | Punto de entrada. Define los *endpoints* HTTP, inicializa los servicios y ejecuta el bucle de **Gossip** en segundo plano. |
| **Gossip Service** | `gossip.py` | Implementa el protocolo **Gossip**. Intercambia versiones de datos (`kv_versions`) y salud del nodo con los *peers*. Se encarga de la **reconciliación** (*fetch* de claves faltantes) para replicar datos. |
| **KVStore** | `kvstore.py` | Almacén de clave-valor local. Asigna y gestiona el **versionamiento** (números incrementales) para cada clave, lo que es esencial para la lógica de replicación. |
| **Scheduler** | `scheduler.py` | Gestión de tareas. Mecanismo simple para la aceptación y gestión de tareas de cálculo. |
| **ML Models** | `models/` | Implementación de modelos básicos de Machine Learning (Regresión Lineal, SVM, etc.) con **NumPy**. |

---

# Pruebas del API de Modelos de IA

## 1. Regresión Lineal (linear_regression)

### A. Entrenamiento
```bash
curl -X POST http://10.0.0.13:8000/train_model/linear_regression \
     -H "Content-Type: application/json" \
     -d '{
           "X": [[1.0], [2.0], [3.0], [4.0]],
           "y": [2.0, 4.0, 6.0, 8.0]
         }'
         
Respuesta esperada:

{"status":"trained","model":"linear_regression"}

B. Predicción
curl -X POST http://10.0.0.13:8000/predict_model/linear_regression \
     -H "Content-Type: application/json" \
     -d '{
           "X": [[5.0], [6.0]]
         }'


Respuesta esperada:

{"predictions": [10.0, 12.0]}

2. Perceptrón Multicapa (mlp)
A. Entrenamiento
curl -X POST http://10.0.0.13:8000/train_model/mlp \
     -H "Content-Type: application/json" \
     -d '{
           "X": [[1.0], [2.0], [3.0], [4.0]],
           "y": [2.0, 4.0, 6.0, 8.0]
         }'


Respuesta esperada:

{"status":"trained","model":"mlp"}

B. Predicción
curl -X POST http://10.0.0.13:8000/predict_model/mlp \
     -H "Content-Type: application/json" \
     -d '{
           "X": [[5.0], [6.0]]
         }'


Respuesta esperada (aprox.):

{"predictions": [10.0, 12.0]}

3. Máquina de Vectores de Soporte (svm)
A. Entrenamiento
curl -X POST http://10.0.0.13:8000/train_model/svm \
     -H "Content-Type: application/json" \
     -d '{
           "X": [[1.0, 1.0], [2.0, 2.0], [3.0, 3.0], 
                 [7.0, 7.0], [8.0, 8.0], [9.0, 9.0]],
           "y": [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
         }'


Respuesta esperada:

{"status":"trained","model":"svm"}

B. Predicción
curl -X POST http://10.0.0.13:8000/predict_model/svm \
     -H "Content-Type: application/json" \
     -d '{
           "X": [[4.0, 4.0], [10.0, 10.0]]
         }'


Respuesta esperada:

{"predictions": [0.0, 1.0]}

4. Árbol de Decisión (decision_tree)
A. Entrenamiento
curl -X POST http://10.0.0.13:8000/train_model/decision_tree \
     -H "Content-Type: application/json" \
     -d '{
           "X": [[1.0, 1.0], [2.0, 2.0], [3.0, 3.0],
                 [7.0, 7.0], [8.0, 8.0], [9.0, 9.0]],
           "y": [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
         }'


Respuesta esperada:

{"status":"trained","model":"decision_tree"}

B. Predicción
curl -X POST http://10.0.0.13:8000/predict_model/decision_tree \
     -H "Content-Type: application/json" \
     -d '{
           "X": [[4.0, 4.0], [10.0, 10.0]]
         }'


Respuesta esperada:

{"predictions": [0.0, 1.0]}

5. Regresión Logística (logistic_regression)
A. Entrenamiento
curl -X POST http://10.0.0.13:8000/train_model/logistic_regression \
     -H "Content-Type: application/json" \
     -d '{
           "X": [[1.0, 1.0], [2.0, 2.0], [3.0, 3.0],
                 [7.0, 7.0], [8.0, 8.0], [9.0, 9.0]],
           "y": [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
         }'


Respuesta esperada:

{"status":"trained","model":"logistic_regression"}

B. Predicción
curl -X POST http://10.0.0.13:8000/predict_model/logistic_regression \
     -H "Content-Type: application/json" \
     -d '{
           "X": [[4.0, 4.0], [10.0, 10.0]]
         }'


Respuesta esperada:

{"predictions": [0.0, 1.0]}