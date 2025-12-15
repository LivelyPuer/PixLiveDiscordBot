import json
import asyncio
from typing import Any, Dict
import aiofiles
import os


class StateStore:
    def __init__(self, path: str):
        self.path = path
        self._lock = asyncio.Lock()
        os.makedirs(os.path.dirname(path), exist_ok=True)

    async def _read(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            return {}
        async with aiofiles.open(self.path, "r") as f:
            content = await f.read()
            if not content:
                return {}
            return json.loads(content)

    async def _write(self, data: Dict[str, Any]):
        async with aiofiles.open(self.path, "w") as f:
            await f.write(json.dumps(data, indent=2))

    async def get(self, key: str, default=None):
        async with self._lock:
            data = await self._read()
            return data.get(key, default)

    async def set(self, key: str, value):
        async with self._lock:
            data = await self._read()
            data[key] = value
            await self._write(data)

    async def update(self, key: str, updater):
        async with self._lock:
            data = await self._read()
            cur = data.get(key, None)
            data[key] = updater(cur)
            await self._write(data)
