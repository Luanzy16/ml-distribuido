import asyncio
import httpx
import time
from typing import Dict, Any
from .utils import split_peers
from .kvstore import KVStore

class GossipService:
    def __init__(self, node_id: str, peers: str, kv: KVStore, interval: float = 3.0):
        self.node_id = node_id
        self.peers_raw = peers or ""
        self.peers = split_peers(peers)
        self.kv = kv
        self.interval = interval
        self._client = httpx.AsyncClient(timeout=5.0)
        self.view: Dict[str, Dict[str, Any]] = {}

    def known_peers(self):
        return list(self.view.keys())

    async def start(self):
        while True:
            await self._gossip_round()
            await asyncio.sleep(self.interval)

    async def _gossip_round(self):
        payload = {
            "node_id": self.node_id,
            "timestamp": time.time(),
            "resources": {"cpu": 0.1},
            "kv_versions": self.kv.versions()
        }
        for p in self.peers:
            # CORRECCIÓN: Definir la URL base separada de la URL del endpoint /gossip
            base_url = f"http://{p}"
            gossip_url = f"{base_url}/gossip"
            try:
                r = await self._client.post(gossip_url, json=payload)
                if r.status_code == 200:
                    data = r.json()
                    # Pasamos la base_url limpia (http://ip:port) a _merge_remote
                    await self._merge_remote(data, base_url) 
            except Exception:
                pass

    async def handle_remote(self, remote: Dict[str, Any]):
        # Si no hay URL, usamos la URL por defecto (http://node_id), que puede fallar.
        # Esto solo se usa si un nodo externo llama a /gossip directamente.
        await self._merge_remote(remote, None)

    async def _merge_remote(self, data: Dict[str, Any], url: str = None):
        rid = data.get("node_id")
        if not rid:
            return

        # Si url es None, intentamos construir una URL por defecto
        # Si url proviene de _gossip_round, ya es la URL base correcta
        self.view[rid] = {"last_seen": time.time(), "url": url or f"http://{rid}", "resources": data.get("resources", {})}\

        remote_versions = data.get("kv_versions", {})
        my_versions = self.kv.versions()

        for k, vver in remote_versions.items():
            if vver > my_versions.get(k, 0):
                if url:
                    try:
                        async with httpx.AsyncClient(timeout=3.0) as c:
                            # Con la corrección en _gossip_round, self.view[rid]['url'] es ahora solo http://ip:port
                            # La URL de fetch será correcta: http://ip:port/kv/key
                            fetch_url = f"{self.view[rid]['url'].rstrip('/')}/kv/{k}"
                            print(f"DEBUG: FETCHING missing key '{k}' (version {vver}) from {rid} at {fetch_url}") # LOG DE DIAGNÓSTICO
                            
                            resp = await c.get(fetch_url)
                            
                            if resp.status_code == 200:
                                data = resp.json()
                                value = data.get("value")
                                print(f"DEBUG SUCCESS: Key '{k}' fetched. Status: 200. Value: {value}") # LOG DE DIAGNÓSTICO
                                self.kv.handle_remote_put(k, value, vver)
                            else:
                                print(f"DEBUG ERROR: Failed to fetch key '{k}'. Status: {resp.status_code}") # LOG DE DIAGNÓSTICO
                                
                    except Exception as e:
                        print(f"DEBUG EXCEPTION: Failed to fetch key '{k}'. Error: {type(e).__name__} - {e}") # LOG DE DIAGNÓSTICO
                        pass