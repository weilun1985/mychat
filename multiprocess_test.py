import asyncio
import multiprocessing,logging
import random
import threading
import time

logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] [%(process)d] [%(thread)d] [%(levelname)s] [%(name)s] [%(processName)s/'
                               '%(funcName)s] %(message)s')
async def task_o(name,q_in,q_out):
    print(f'启动 task: {name}')
    while True:
        question=await q_in.get()
        #print(f'task-receive({name})-> ',question)
        t=random.uniform(0,5)
        await asyncio.sleep(0.1)
        #time.sleep(t)
        answer=f'this is answer: worker={name},question={question} sleep={t}'
        #print(f'task-result({name})->',answer)
        #await f_a(answer)
        await q_out.put(answer)
        print(f'ok-{name} {question}')
        #await queue_out.put(answer)
    print(f'停止 task_o: {name}')

async def worker0(q_in,q_out):
    tasks = []
    for i in range(5):
        task = asyncio.create_task(task_o(f'name-{i}', q_in, q_out))
        tasks.append(task)
    await asyncio.gather(*tasks)

def worker(q_in,q_out):
    asyncio.run(worker0(q_in, q_out))

def multi_process_run(q,q2):
    p = multiprocessing.Process(target=worker, args=(q, q2))
    p.start()
    logging.info('multiprocess start...')
    return p

if __name__=='__main__':
    logging.info('main start...')
    q = multiprocessing.Queue()
    q2 = multiprocessing.Queue()
    p=multi_process_run(q,q2)
    print(p)
    print('')



    def func(i):
        q.put('hello %d' % i)
        r = q2.get()
        print(f'got r:{r}')

    for i in range(5):
        thrd=threading.Thread(target=func,args=[i])
        thrd.start()
        #logging.info('result: %s'%r)
    #input('press any key for next.')
    #f1(None)
    p.join()