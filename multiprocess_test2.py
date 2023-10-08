import asyncio
import multiprocessing,logging,os
import random
import threading

logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] [%(process)d] [%(thread)d] [%(levelname)s] [%(name)s] [%(processName)s/'
                               '%(funcName)s] %(message)s')
logger=logging.getLogger('mt')

async def do_item(a):
    t = random.uniform(0, 5)
    await asyncio.sleep(t)
    return f'out-{a}-sleep-{t}'

async def do_loop(name,q_in:asyncio.Queue,q_out:asyncio.Queue):
    logger.info(f'worker-ready:{name}')
    while True:
        in_a=await q_in.get()
        logger.info(f'\tworker-in:{name} {in_a}')
        out_a=await do_item(in_a)
        #logger.info(f'\tworker-done:{name} {in_a} {out_a}')
        await q_out.put(out_a)
        logger.info(f'\tworker-out:{name} {in_a} {out_a}')

async def do_loop2(name):
    logger.info(f'worker-ready:{name}')
    while True:
        in_a=yield
        logger.info(f'\tworker-in:{name} {in_a}')
        out_a=await do_item(in_a)
        #logger.info(f'\tworker-done:{name} {in_a} {out_a}')
        yield out_a
        logger.info(f'\tworker-out:{name} {in_a} {out_a}')

async def do_loop_wrapper(fn,instr):
    await anext(fn)
    result=await fn.asend(instr)
    print(result)
    await anext(fn)
    return result



def start_thread_loop(loop):
    # 定义一个跑事件循环的线程函数
    logger.info("start_thread_loop")
    asyncio.set_event_loop(loop)
    loop.run_forever()

def work():
    loop = asyncio.get_event_loop()
    # 在子线程中运行事件循环，run_forever
    t = threading.Thread(target=start_thread_loop, args=(loop,))
    t.start()
    names = ['A', 'B', 'C', 'D']
    q_in = asyncio.Queue()
    q_out = asyncio.Queue()
    for name in names:
        task=do_loop(name,q_in,q_out)
        asyncio.run_coroutine_threadsafe(task, loop)
    async def func0(question):
        await q_in.put(question)
        result=await q_out.get()
        #return result


    def func(question):
        # task=func0(question)
        # ff=asyncio.run_coroutine_threadsafe(task, loop)
        # return ff.result()
        f1=q_in.put(question)
        f2=q_out.get()
        asyncio.run_coroutine_threadsafe(f1, loop)
        result=asyncio.run_coroutine_threadsafe(f2, loop)
        #print(question,result)
    return func


def worker_process(q_in, q_out):
    logger.info(f'processor-running: {os.getpid()} {threading.current_thread().ident}')
    func=work()
    while True:
        instr=q_in.get()
        #print(instr)
        out=func(instr)
    logger.info(f'processor-end: {os.getpid()} {threading.current_thread().ident}')
    pass

def create_worker_proces(q_in, q_out):
    p = multiprocessing.Process(target=worker_process, args=(q_in, q_out))
    p.start()
    logger.info('-->worker-process start...')
    return p

def caller(q_in,q_out,a):
    logger.info(f'caller-thread running: {a} {os.getpid()} {threading.current_thread().ident}')
    q_in.put(a)
    # for i in range(1,5):
    #     a=i%4+1
    #     #logger.info(f'输入是：{i}')
    #     q_in.put(i)
    #     #time.sleep(0.1)
    #     #r=q_out.get()
    #    # print('结果是：',r)


def create_caller(q_in, q_out):
    for i in range(1, 5):
        thr=threading.Thread(target=caller,args=(q_in,q_out,i))
        thr.start()
    #print('\t-->caller-thread start...')
    #return thr

def run():
    q_in = multiprocessing.Queue()
    q_out = multiprocessing.Queue()
    p = create_worker_proces(q_in, q_out)
    create_caller(q_in,q_out)
    #print('\twait for stop...')
    #c.join()
    logger.info(f'-->caller-thread stop. {os.getpid()} {threading.current_thread().ident}')
    p.join()
    logger.info(f'-->worker-process stop. {os.getpid()} {threading.current_thread().ident}')

def run2():
    fn1 = do_loop2('A')
    c1=do_loop_wrapper(fn1,1)
    c2 = do_loop_wrapper(fn1, 2)
    loop = asyncio.get_event_loop()
    asyncio.run_coroutine_threadsafe(c1, loop)
    asyncio.run_coroutine_threadsafe(c2, loop)
    #task1 = loop.create_task(c1)
    #task2 = loop.create_task(c2)
    loop.run_forever()

if __name__=="__main__":
    logger.info(f"主线程-开始运行: {os.getpid()} {threading.current_thread().ident}")
    run()
    #run2()
    logger.info(f"主线程-运行结束: {os.getpid()} {threading.current_thread().ident}")