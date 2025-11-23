import asyncio

class Scheduler:
    def __init__(self, node_id, peers, kv, gossip=None):
        self.node_id = node_id
        self.peers = peers
        self.kv = kv
        self.gossip = gossip

    async def submit_task(self, task):
        # Simple policy: always accept
        return {"status": "accepted", "node": self.node_id}

    def can_accept(self):
        return True
