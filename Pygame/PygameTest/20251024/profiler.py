# -------------------- profiler.py --------------------
import time

class Profiler:
    def __init__(self):
        self.data = {}


    def start(self, name):
        self.data[name] = {'start': time.time(), 'elapsed': self.data.get(name, {}).get('elapsed', 0)}


    def stop(self, name):
        if name in self.data and 'start' in self.data[name]:
            elapsed = (time.time() - self.data[name]['start']) * 1000
            self.data[name]['elapsed'] += elapsed
            self.data[name]['start'] = None


    def report(self):
        print("--- Performance Report (ms/frame) ---")
        for name, val in self.data.items():
            print(f"{name:<15}: {val['elapsed']:.2f} ms")
            print("------------------------------------\n")
            for name in self.data:
                self.data[name]['elapsed'] = 0