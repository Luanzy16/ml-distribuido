# app/scheduler.py
import httpx
import asyncio
import random
from typing import Dict, Any, List
from .utils import split_peers

class Scheduler:
    def __init__(self, node_id: str, peers: str, kv, gossip):
        self.node_id = node_id
        self.peers_raw = peers or ""
        self.peers = split_peers(peers)
        self.kv = kv
        self.gossip = gossip
        self._client = httpx.AsyncClient(timeout=8.0)

    def can_accept(self) -> bool:
        # simple policy: accept if local queue small (improve with metrics)
        return True

    async def submit_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        # Leaderless scheduling: compute scores and pick best node (here: prefer nodes discovered via gossip)
        candidates = [self.node_id] + self.peers
        # Randomized scoring: prefer local 20% of the time
        if random.random() < 0.2:
            pick = self.node_id
        else:
            # pick a discovered peer if any
            known = self.gossip.known_peers()
            if known:
                pick = random.choice(known)
                # known entries are node_ids; map to URL via peers list heuristic
                # if pick looks like ip:port use directly
                if ":" in pick:
                    pick_url = pick
                else:
                    # try first peer URL
                    pick_url = (self.peers[0] if self.peers else None)
            else:
                pick = self.node_id
        if pick == self.node_id:
            # run locally (caller expects a response)
            # simulate acceptance
            return {"status": "scheduled_local", "node": self.node_id}
        else:
            # remote assign
            target_url = pick if ":" in pick else (self.peers[0] if self.peers else pick)
            try:
                resp = await self._client.post(f"http://{target_url}/assign_task", json=task)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return {"status": "error_remote", "code": resp.status_code}
            except Exception:
                return {"status": "error_remote", "node": target_url}
