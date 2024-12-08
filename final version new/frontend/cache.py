import threading

class MemCache:
    def __init__(self) -> None:
        self.mem_cache={}
        self.lock=threading.Lock()

    def add(self, key, val)->None:
        with self.lock:
            self.mem_cache[key]=val
    
    def rm(self, key)->None:
        with self.lock:
            if key in self.mem_cache:
                del self.mem_cache[key]
    
    def get(self, key)->dict:
        with self.lock:
            return self.mem_cache.get(key,None)
    
