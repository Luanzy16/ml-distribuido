# app/kvstore.py
import time
import asyncio
import httpx
from typing import Dict, Any, List

class KVStore:
    def __init__(self, node_id: str):
        self.node_id = node_id
        # store: key -> {value, version, ts}
        self.store: Dict[str, Dict[str, Any]] = {}
        self._client = httpx.AsyncClient(timeout=5.0)

    def put(self, key: str, value: Any):
        now = time.time()
        cur = self.store.get(key)
        if cur:
            ver = cur["version"] + 1
        else:
            ver = 1
        self.store[key] = {"value": value, "version": ver, "ts": now}
        return True

    def get(self, key: str):
        cur = self.store.get(key)
        if not cur:
            return None
        return {"value": cur["value"], "version": cur["version"], "ts": cur["ts"]}

    def versions(self):
        return {k: v["version"] for k, v in self.store.items()}

    async def replicate(self, key: str, peers: str, replicate_to: int = 2):
        peer_list = [p for p in peers.split(",") if p]
        payload = {"value": self.store[key]["value"], "version": self.store[key]["version"]}
        tasks = []
        for p in peer_list[:replicate_to]:
            tasks.append(self._push(p, key, payload))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _push(self, peer: str, key: str, payload: Dict[str, Any]):
        try:
            await self._client.put(f"http://{peer}/kv/{key}", json={"value": payload["value"], "version": payload["version"]})
        except Exception:
            pass

    async def background_reconcile(self, peers: str):
        # Periodically check peers' kv_versions and request newer keys
        while True:
            peer_list = [p for p in peers.split(",") if p]
            for p in peer_list:
                try:
                    r = await self._client.get(f"http://{p}/state")
                    if r.status_code == 200:
                        remote = r.json()
                        remote_versions = remote.get("kv_versions", {})
                        for k, rv in remote_versions.items():
                            myv = self.versions().get(k, 0)
                            if rv > myv:
                                # fetch from peer
                                try:
                                    res = await self._client.get(f"http://{p}/kv/{k}")
                                    if res.status_code == 200:
                                        data = res.json()
                                        # apply
                                        self.store[k] = {"value": data.get("value"), "version": data.get("version"), "ts": data.get("ts", time.time())}
                                except Exception:
                                    pass
                except Exception:
                    pass
            await asyncio.sleep(10)

    # handler used by GossipService to apply remote kv puts (sync)
    def handle_remote_put(self, key: str, value: Any, version: int):
        cur = self.store.get(key)
        if (cur is None) or (version > cur["version"]):
            self.store[key] = {"value": value, "version": version, "ts": time.time()}
