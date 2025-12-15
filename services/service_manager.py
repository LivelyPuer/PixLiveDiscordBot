from typing import Dict


class ServiceManager:
    def __init__(self):
        self._services: Dict[str, object] = {}
        self._paused: Dict[str, bool] = {}

    def register(self, name: str, service):
        self._services[name] = service
        self._paused[name] = False

    def get(self, name: str):
        return self._services.get(name)

    def pause(self, name: str) -> bool:
        if name in self._services:
            self._paused[name] = True
            # call stop if available
            svc = self._services[name]
            if hasattr(svc, "stop"):
                svc.stop()
            return True
        return False

    def resume(self, name: str) -> bool:
        if name in self._services:
            self._paused[name] = False
            svc = self._services[name]
            if hasattr(svc, "start"):
                # starting will run loop; caller is responsible for awaiting
                return True
        return False

    def list_names(self):
        return list(self._services.keys())
