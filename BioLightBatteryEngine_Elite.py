# BioLight v1.4 - Passive Entropy Engine
# Author: Andrea Mascheroni (Ladaxia)
# License: Ladaxia_Public_License
# Description: This module implements the passive entropy battery that accumulates raw entropy over time,
#              selecting only statistically elite samples for long-term retention.

import os
import time
import json
import base64
import numpy as np
from collections import Counter
from math import log2
from typing import List


class EliteSample:
    def __init__(self, data: bytes, score: float, timestamp: float, source: str):
        self.data = data
        self.score = score
        self.timestamp = timestamp
        self.source = source

    def to_json(self):
        return {
            "score": round(self.score, 4),
            "timestamp": self.timestamp,
            "source": self.source,
            "data": base64.b64encode(self.data).decode("utf-8")
        }


class BioLightBatteryEngineElite:

    def try_composite_input(self):
        import random
        def maybe_include(source, probability=1.0):
            if random.random() <= probability:
                real = self.read_real_input(source)
                return real if real else self.simulate_input(source)
            return b""

        parts = [
            maybe_include("screen", 1.0),
            maybe_include("screen_partial", 1.0),
            maybe_include("audio", 0.75),
            maybe_include("ram", 0.5),
            maybe_include("kernel_entropy_pool", 0.5),
            maybe_include("adc_noise", 0.33),
            maybe_include("accel_gyro", 0.33),
        ]

        combined = b"".join(parts)
        self.add(combined, "composite_probabilistic_weights")
    def __init__(self):
        self.heap: List[EliteSample] = []
        self.max_size = 100
        self.last_real_time = {}

    def entropy(self, data: bytes) -> float:
        freq = Counter(data)
        total = len(data)
        return -sum((n / total) * log2(n / total) for n in freq.values())

    def add(self, data: bytes, source: str):
        score = self.entropy(data)
        if score >= 7.8:
            self.heap.append(EliteSample(data, score, time.time(), source))
            self.heap.sort(key=lambda s: s.score, reverse=True)
            self.heap = self.heap[:self.max_size]

    def read_real_input(self, source: str) -> bytes:
        now = time.time()
        min_interval = 0.05

        if source in self.last_real_time and now - self.last_real_time[source] < min_interval:
            return None

        self.last_real_time[source] = now

        try:
            if source == "screen":
                with open("/dev/fb0", "rb") as f:
                    return f.read(12288)
            elif source == "ram":
                with open("/dev/mem", "rb") as f:
                    return f.read(512)
            elif source == "kernel_entropy_pool":
                with open("/dev/random", "rb") as f:
                    return f.read(512)
            elif source == "screen_partial":
                return open("/dev/fb0", "rb").read(3072)
        except Exception:
            return None
        return None

    def simulate_input(self, source: str) -> bytes:
        if source == "screen":
            return np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8).tobytes()
        elif source == "ram":
            return os.urandom(512)
        elif source == "audio":
            return np.random.randint(-128, 127, 1024, dtype=np.int8).tobytes()
        elif source == "screen_partial":
            return np.random.randint(0, 256, size=(32, 32, 3), dtype=np.uint8).tobytes()
        elif source == "accel_gyro":
            return np.random.normal(0, 0.5, (128, 3)).astype(np.float32).tobytes()
        elif source == "kernel_entropy_pool":
            return np.random.randint(0, 256, 512, dtype=np.uint8).tobytes()
        elif source == "adc_noise":
            return np.random.randint(-128, 127, 256, dtype=np.int8).tobytes()
        raise ValueError("Unsupported simulated input source")

        sources = [
            "audio",
            "screen_partial",
            "screen",
            "ram",
            "kernel_entropy_pool",
            "adc_noise",
            "accel_gyro"
        ]

        for src in sources:
            real = self.read_real_input(src)
            if real:
                parts.append(real)
                labels.append(src)
            else:
                parts.append(self.simulate_input(src))
                labels.append(f"{src}_fallback")

        combined = b"".join(parts)
        self.add(combined, f"composite_real+fallback({'+'.join(labels)})")

    def export_audit_log(self) -> str:
        return json.dumps({
            "samples": [s.to_json() for s in self.heap]
        }, indent=2)
