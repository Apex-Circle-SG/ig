import os
import json
import fcntl
import hashlib
import tempfile
from typing import Any, Dict, Optional


class PersistentMemory:
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.path.dirname(os.path.abspath(__file__))
        self.lock_file = os.path.join(self.base_path, '.memory.lock')
        self.lock_handle = None

    def _calculate_hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _acquire_lock(self) -> None:
        if self.lock_handle is None:
            self.lock_handle = open(self.lock_file, 'w')
        fcntl.flock(self.lock_handle, fcntl.LOCK_EX)

    def _release_lock(self) -> None:
        if self.lock_handle is not None:
            fcntl.flock(self.lock_handle, fcntl.LOCK_UN)
            self.lock_handle.close()
            self.lock_handle = None
            if os.path.exists(self.lock_file):
                os.unlink(self.lock_file)

    def load(self, filename: str, default: Any = None) -> Any:
        self._acquire_lock()
        try:
            full_path = os.path.join(self.base_path, filename)
            if not os.path.exists(full_path):
                return default

            with open(full_path, 'rb') as f:
                content = f.read()

            if len(content) < 65:
                return default

            stored_hash = content[:64].decode('ascii')
            data = content[65:]

            calculated_hash = self._calculate_hash(data)
            if calculated_hash != stored_hash:
                return default

            return json.loads(data.decode('utf-8'))
        except Exception:
            return default
        finally:
            self._release_lock()

    def save(self, filename: str, data: Any) -> bool:
        self._acquire_lock()
        try:
            full_path = os.path.join(self.base_path, filename)
            serialized = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
            file_hash = self._calculate_hash(serialized)
            final_content = f"{file_hash}\n".encode('utf-8') + serialized

            temp_dir = os.path.dirname(full_path)
            fd, temp_path = tempfile.mkstemp(dir=temp_dir, prefix='.tmp_', suffix='.json')
            try:
                with os.fdopen(fd, 'wb') as f:
                    f.write(final_content)
                os.rename(temp_path, full_path)
                return True
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        except Exception:
            return False
        finally:
            self._release_lock()

    def transaction(self):
        return MemoryTransaction(self)

    def __enter__(self):
        self._acquire_lock()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._release_lock()


class MemoryTransaction:
    def __init__(self, memory: PersistentMemory):
        self.memory = memory
        self.pending = {}

    def __enter__(self):
        self.memory._acquire_lock()
        return self

    def set(self, filename: str, data: Any) -> None:
        self.pending[filename] = data

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                for filename, data in self.pending.items():
                    self.memory.save(filename, data)
        finally:
            self.memory._release_lock()


memory = PersistentMemory()
