import threading,queue,time
class TaskQueue:
    def __init__(self,workers=2):
        self.queue=queue.Queue(); self.results={}; self.workers=[]
        self.task_id=0; self.lock=threading.Lock()
        for _ in range(workers):
            t=threading.Thread(target=self._worker,daemon=True); t.start(); self.workers.append(t)
    def _worker(self):
        while True:
            tid,fn,args,kwargs=self.queue.get()
            try:
                result=fn(*args,**kwargs)
                with self.lock: self.results[tid]={'status':'done','result':result}
            except Exception as e:
                with self.lock: self.results[tid]={'status':'error','error':str(e)}
            self.queue.task_done()
    def submit(self,fn,*args,**kwargs):
        with self.lock: self.task_id+=1; tid=self.task_id
        self.results[tid]={'status':'pending'}
        self.queue.put((tid,fn,args,kwargs))
        return tid
    def get_result(self,tid):
        with self.lock: return self.results.get(tid)
    def wait_all(self): self.queue.join()
if __name__=="__main__":
    tq=TaskQueue(workers=2)
    ids=[]
    for i in range(5):
        tid=tq.submit(lambda x: x**2, i); ids.append(tid)
    tq.wait_all()
    results=[tq.get_result(tid)['result'] for tid in ids]
    assert results==[0,1,4,9,16]
    err_id=tq.submit(lambda: 1/0); tq.wait_all()
    assert tq.get_result(err_id)['status']=='error'
    print(f"Results: {results}")
    print("All tests passed!")
