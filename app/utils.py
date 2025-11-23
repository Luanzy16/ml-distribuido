import os

def load_env():
    cfg = {}
    with open(".env") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            key, val = line.strip().split("=", 1)
            cfg[key] = val
    return cfg

def split_peers(peers: str):
    if not peers:
        return []
    return [p.strip() for p in peers.split(",")]
