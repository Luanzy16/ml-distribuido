# app/utils.py
import os
from typing import Dict, Any, List

def load_env() -> Dict[str, str]:
    # loads .env in working dir
    res = {}
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                k, v = s.split("=", 1)
                res[k.strip()] = v.strip()
    # ensure default keys
    res.setdefault("NODE_ID", "node")
    res.setdefault("PORT", "8000")
    res.setdefault("PEERS", "")
    return res

def split_peers(peers: str) -> List[str]:
    if not peers:
        return []
    return [p.strip() for p in peers.split(",") if p.strip()]
