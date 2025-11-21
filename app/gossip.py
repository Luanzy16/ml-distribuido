# app/gossip.py
import asyncio
import httpx
import time
from typing import List, Dict, Any
from .utils import split_peers

class GossipService:
    def __init__(self, node_id: str, peers: str, kv, interval: float = 3.0):
        self.node_id = node_id
        self.peers_raw = peers or ""
        self.peers = split_peers(peers)
        self.kv = kv
        self.interval = interval
        self._client = httpx.AsyncClient(timeout=5.0)
        # local view of peers: node_id -> {'last_seen': ts, 'url': url, 'resources': {...}}
        self.view: Dict[str, Dict[str, Any]] = {}

    def known_peers(self) -> List[str]:
        return list(self.view.keys())

    async def start(self):
        while True:
            await self._gossip_round()
            await asyncio.sleep(self.interval)

    async def _gossip_round(self):
        payload = {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "resources": {"cpu": 0.1},  # placeholder; extend with psutil if needed
            "kv_versions": self.kv.versions()
        }
        # try all peers (small cluster). For very large clusters sample random subset.
        for p in self.peers:
            url = f"http://{p}/gossip"
            try:
                r = await self._client.post(url, json=payload)
                if r.status_code == 200:
                    data = r.json()
                    await self._merge_remote(data, url)
            except Exception:
                # ignore unreachable peers; they'll be retried next round
                pass

    async def handle_remote(self, remote: Dict[str, Any]):
        # Called when another node posts /gossip to us
        # Merge remote info and optionally return our view (not used)
        await self._merge_remote(remote, None)

    async def _merge_remote(self, data: Dict[str, Any], url: str = None):
        rid = data.get("node_id")
        if not rid:
            return
        entry = {"last_seen": time.time(), "url": url or data.get("api_url") or f"http://{rid}", "resources": data.get("resources", {})}
        self.view[rid] = entry
        # Check KV versions and optionally request missing keys (simple approach)
        remote_versions = data.get("kv_versions", {})
        my_versions = self.kv.versions()
        for k, vver in remote_versions.items():
            myver = my_versions.get(k, 0)
            if vver > myver:
                # request key from remote
                if url:
                    # if we know remote url, request /kv/<key>
                    try:
                        async with httpx.AsyncClient(timeout=3.0) as c:
                            resp = await c.get(f"{entry['url'].rstrip('/')}/kv/{k}")
                            if resp.status_code == 200:
                                payload = resp.json()
                                self.kv.handle_remote_put(k, payload.get("value"), payload.get("version"))
                    except Exception:
                        pass
