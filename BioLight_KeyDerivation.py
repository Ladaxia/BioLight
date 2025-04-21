# BioLight v1.4 - Key Derivation Module
# Author: Andrea Mascheroni (Ladaxia)
# License: Ladaxia_Public_License
# Description: This module performs key derivation from selected entropy blocks using SHAKE256 or compatible XOFs.


import base64
import time
from hashlib import shake_256, sha3_512
from typing import List

try:
    import blake3
except ImportError:
    blake3 = None


def derive_key(heap: List, method: str = "shake256", top_n: int = 32, key_bytes: int = 32):
    """Derive a final cryptographic key using elite entropy and the selected hash function."""
    if method not in {"shake256", "sha3_512", "blake3"}:
        raise ValueError("Unsupported method")

    top_blocks = sorted(heap, key=lambda s: s.score, reverse=True)[:top_n]
    combined = b"".join(block.data for block in top_blocks)

    if method == "shake256":
        final_key = shake_256(combined).digest(key_bytes)
    elif method == "sha3_512":
        final_key = sha3_512(combined).digest()[:key_bytes]
    elif method == "blake3":
        if not blake3:
            raise ImportError("blake3 module not available")
        final_key = blake3.blake3(combined).digest(length=key_bytes)

    audit = {
        "method": f"{method}_from_elite_raw",
        "key_bits": key_bytes * 8,
        "timestamp": time.time(),
        "source_blocks": [
            {
                "score": round(b.score, 4),
                "source": b.source,
                "timestamp": b.timestamp
            } for b in top_blocks
        ],
        "final_key_base64": base64.b64encode(final_key).decode("utf-8")
    }

    return final_key, audit
