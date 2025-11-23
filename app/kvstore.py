import asyncio
import time

class KVStore:
    def __init__(self, node_id):
        self.node_id = node_id
        self.store = {}        # key -> value
        self.versions_dict = {} # key -> version

    def put(self, key, value):
        self.store[key] = value
        self.versions_dict[key] = self.versions_dict.get(key, 0) + 1

    def get(self, key):
        return self.store.get(key)

    def versions(self):
        return self.versions_dict.copy()

    async def replicate(self, key, peers, replicate_to=1):
        # placeholder: real network calls would go here
        await asyncio.sleep(0.1)

    async def background_reconcile(self, peers):
        while True:
            # in a real system, we could fetch missing keys
            await asyncio.sleep(5)

    def handle_remote_put(self, key, value, version):
        local_version = self.versions_dict.get(key, 0)
        if version > local_version:
            self.store[key] = value
            self.versions_dict[key] = version
