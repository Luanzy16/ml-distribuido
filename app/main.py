import os
import asyncio
from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import numpy as np

from .gossip import GossipService
from .scheduler import Scheduler
from .kvstore import KVStore
from .utils import load_env
from .visual import plot_predictions
from .models.linear_regression import LinearRegression
from .models.logistic_regression import LogisticRegression
from .models.svm import SVM
from .models.mlp import MLP

cfg = load_env()
NODE_ID = cfg["NODE_ID"]
PORT = int(cfg["PORT"])
PEERS = cfg["PEERS"]
GOSSIP_INTERVAL = float(cfg.get("GOSSIP_INTERVAL", 3.0))
REPLICATE_TO = int(cfg.get("REPLICATE_TO", 2))

app = FastAPI(title=f"gossip-node-{NODE_ID}")

kv = KVStore(node_id=NODE_ID)
gossip = GossipService(node_id=NODE_ID, peers=PEERS, kv=kv, interval=GOSSIP_INTERVAL)
scheduler = Scheduler(node_id=NODE_ID, peers=PEERS, kv=kv, gossip=gossip)

tasks: Dict[str, Dict[str, Any]] = {}
models: Dict[str, Any] = {}

class TaskIn(BaseModel):
    id: str
    kind: str
    payload: Dict[str, Any]

# =========================================================================
# MODELOS DE ENTRADA CORREGIDOS PARA FASTAPI/PYDANTIC
# =========================================================================

class PredictionIn(BaseModel):
    X: List[List[float]]

class KVPutIn(BaseModel):
    value: Any

# =========================================================================
# LIFESPAN EVENTS
# =========================================================================

@app.on_event("startup")
async def startup_event():
    # Iniciar el proceso de gossip en segundo plano
    asyncio.create_task(gossip.start())
    print(f"Node {NODE_ID} started and gossip running...")

# =========================================================================
# CORE ENDPOINTS
# =========================================================================

@app.get("/state")
async def get_state():
    return {
        "node_id": NODE_ID,
        "peers": gossip.known_peers(),
        "tasks": tasks,
        "kv_versions": kv.versions(),
    }

@app.post("/gossip")
async def receive_gossip(payload: Dict[str, Any] = Body(...)):
    await gossip.handle_remote(payload)
    return {"ok": True, "node": NODE_ID}

@app.post("/submit_task")
async def submit_task(task: TaskIn):
    res = await scheduler.submit_task(task.dict())
    return res

# =========================================================================
# MACHINE LEARNING ENDPOINTS (CON CORRECCIÓN DE INPUT)
# =========================================================================

@app.post("/train_model/{model_name}")
async def train_model(model_name: str, X: List[List[float]], y: List[float]):
    X_np = np.array(X)
    y_np = np.array(y)
    
    if model_name == "linear_regression":
        model = LinearRegression()
    elif model_name == "logistic_regression":
        model = LogisticRegression()
    elif model_name == "svm":
        model = SVM()
    elif model_name == "mlp":
        model = MLP(input_size=X_np.shape[1])
    else:
        raise HTTPException(400, f"{model_name} not implemented")
        
    model.fit(X_np, y_np)
    models[model_name] = model
    return {"status": "trained", "model": model_name}

@app.post("/predict_model/{model_name}")
async def predict_model(model_name: str, input_data: PredictionIn): # <--- CORREGIDO
    if model_name not in models:
        raise HTTPException(400, "Model not trained")
    
    model = models[model_name]
    X_np = np.array(input_data.X)
    
    predictions = model.predict(X_np).tolist()
    return {"predictions": predictions}

@app.post("/plot")
async def plot(y_true: List[float], y_pred: List[float]):
    img_b64 = plot_predictions(y_true, y_pred)
    return {"image_b64": img_b64}

# =========================================================================
# KVSTORE ENDPOINTS (NUEVOS PARA PRUEBA DE GOSSIP)
# =========================================================================

@app.get("/kv/{key}")
async def kv_get(key: str):
    """Obtiene una clave de la KVStore local. Usado por Gossip para reconciliar datos."""
    value = kv.get(key)
    if value is None:
        raise HTTPException(404, f"Key '{key}' not found")
    return {"key": key, "value": value}

@app.put("/kv/{key}")
async def kv_put(key: str, item: KVPutIn):
    """Inserta/actualiza una clave en la KVStore local."""
    kv.put(key, item.value)
    return {"status": "stored", "key": key, "value": item.value}