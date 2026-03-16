#!/usr/bin/env python3
"""Distributed task queue with workers, retries, and priorities."""
import threading, queue, time, sys, random

class Task:
    def __init__(self, fn, args=(), priority=0, max_retries=3):
        self.fn=fn;self.args=args;self.priority=priority
        self.max_retries=max_retries;self.retries=0;self.result=None;self.error=None
        self.status="pending";self.id=id(self)
    def __lt__(self,other): return self.priority>other.priority

class TaskQueue:
    def __init__(self, num_workers=3):
        self.q=queue.PriorityQueue(); self.results={}; self.lock=threading.Lock()
        self.workers=[threading.Thread(target=self._worker,daemon=True) for _ in range(num_workers)]
        for w in self.workers: w.start()
    def _worker(self):
        while True:
            task=self.q.get()
            task.status="running"
            try:
                task.result=task.fn(*task.args); task.status="done"
            except Exception as e:
                task.retries+=1
                if task.retries<task.max_retries:
                    task.status="retry"; self.q.put(task)
                else:
                    task.error=e; task.status="failed"
            with self.lock: self.results[task.id]=task
            self.q.task_done()
    def submit(self, fn, args=(), priority=0):
        task=Task(fn,args,priority); self.q.put(task); return task.id
    def wait(self): self.q.join()
    def get_results(self):
        with self.lock: return dict(self.results)

if __name__ == "__main__":
    tq=TaskQueue(3)
    def compute(x):
        time.sleep(random.uniform(0.01,0.05))
        if x==3: raise ValueError("bad input")
        return x**2
    ids=[tq.submit(compute,(i,),priority=i) for i in range(6)]
    tq.wait()
    for tid,task in tq.get_results().items():
        print(f"  Task {task.args}: {task.status} result={task.result} err={task.error}")
