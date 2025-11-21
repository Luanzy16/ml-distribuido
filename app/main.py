# app/main.py
import os
import asyncio
from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

from .gossip import GossipService
from .scheduler import Scheduler
from .kvstore import KVStore
from .utils import load_env

# load env
cfg = load_env()

NODE_ID = cfg["NODE_ID"]
PORT = int(cfg["PORT"])
PEERS = cfg["PEERS"]
GOSSIP_INTERVAL = float(cfg.get("GOSSIP_INTERVAL", 3.0))
REPLICATE_TO = int(cfg.get("REPLICATE_TO", 2))

app = FastAPI(title=f"gossip-node-{NODE_ID}")

# core components
kv = KVStore(node_id=NODE_ID)
gossip = GossipService(node_id=NODE_ID, peers=PEERS, kv=kv, interval=GOSSIP_INTERVAL)
scheduler = Scheduler(node_id=NODE_ID, peers=PEERS, kv=kv, gossip=gossip)

# in-memory running tasks state (task_id -> meta)
tasks: Dict[str, Dict[str, Any]] = {}

class TaskIn(BaseModel):
    id: str
    kind: str
    payload: Dict[str, Any] = {}
    requirements: Dict[str, Any] = {}

@app.on_event("startup")
async def startup():
    # start gossip loop
    asyncio.create_task(gossip.start())
    # start background KV reconciler
    asyncio.create_task(kv.background_reconcile(peers=PEERS))
    # background garbage/cleanup
    asyncio.create_task(cleaner())

async def cleaner():
    while True:
        # simple cleanup of finished tasks
        for tid, md in list(tasks.items()):
            if md.get("status") == "done":
                # keep short time then purge
                if md.get("finished_at", 0) + 30 < asyncio.get_event_loop().time():
                    tasks.pop(tid, None)
        await asyncio.sleep(10)

@app.get("/state")
async def state():
    return {
        "node_id": NODE_ID,
        "peers": gossip.known_peers(),
        "tasks": {k: v.get("status") for k, v in tasks.items()},
        "kv_versions": kv.versions()
    }

@app.post("/gossip")
async def receive_gossip(payload: Dict[str, Any] = Body(...)):
    # payload: {'node_id':..., 'timestamp':..., 'resources':..., 'kv_versions': {...}}
    await gossip.handle_remote(payload)
    return {"ok": True, "node": NODE_ID}

@app.post("/submit_task")
async def submit_task(task: TaskIn):
    # client submits task to this node; scheduler will decide where to run
    res = await scheduler.submit_task(task.dict())
    return res

@app.post("/assign_task")
async def assign_task(task: TaskIn):
    # other node asks this node to run a task
    # accept based on simple local policy
    if scheduler.can_accept():
        tasks[task.id] = {"status": "running", "kind": task.kind, "payload": task.payload, "started_at": asyncio.get_event_loop().time()}
        # run in background
        asyncio.create_task(execute_task(task.id, task.kind, task.payload))
        return {"status": "accepted", "node": NODE_ID}
    else:
        return {"status": "rejected", "node": NODE_ID}

async def execute_task(task_id: str, kind: str, payload: Dict[str, Any]):
    # Basic simulated ML tasks. Replace with real training/inference code.
    try:
        if kind == "matrix_multiply":
            import numpy as np
            n = int(payload.get("n", 200))
            A = np.random.rand(n, n)
            B = np.random.rand(n, n)
            _ = A @ B
            await asyncio.sleep(0.5)
        elif kind == "train_dummy":
            # simulate long job with checkpoints to KV
            steps = int(payload.get("steps", 5))
            for s in range(steps):
                # write checkpoint into kv
                kv.put(f"ckpt:{task_id}:step", {"step": s})
                await asyncio.sleep(1)
        else:
            await asyncio.sleep(float(payload.get("duration", 1.0)))
        tasks[task_id]["status"] = "done"
        tasks[task_id]["finished_at"] = asyncio.get_event_loop().time()
    except Exception as e:
        tasks[task_id]["status"] = "error"
        tasks[task_id]["error"] = str(e)

# KV endpoints (internal)
@app.put("/kv/{key}")
async def kv_put(key: str, body: Dict[str, Any] = Body(...)):
    value = body.get("value")
    if value is None:
        raise HTTPException(400, "value missing")
    kv.put(key, value)
    # replicate in background
    asyncio.create_task(kv.replicate(key, peers=PEERS, replicate_to=REPLICATE_TO))
    return {"ok": True, "key": key}

@app.get("/kv/{key}")
async def kv_get(key: str):
    v = kv.get(key)
    if v is None:
        raise HTTPException(404, "not found")
    return v
