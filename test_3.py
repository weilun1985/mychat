import asyncio
import time,sys
import threading
import concurrent
import os


async def func1():
    print("suspending func1")
    await asyncio.sleep(1)
    print("func1 thred",threading.current_thread().name,threading.current_thread().ident,os.getpid())
    print("resuming func1")
    return "func1"


async def func2():
    print("suspending func2")
    await asyncio.sleep(1)
    print("func2 thred", threading.current_thread().name,threading.current_thread().ident,os.getpid())
    print("resuming func2")
    return "func2"


def callbackfunc(task):
    # 任务回调函数，不中止loop
    print("task 运行结束，结果是： ",task.result(),threading.current_thread().name,threading.current_thread().ident,os.getpid())


def callbackfunc2(task):
    # 任务回调函数，同时中止loop
    print("task 运行结束，结果是： ",task.result(),threading.current_thread().name,threading.current_thread().ident,os.getpid())
    task.get_loop().stop()


def ping(url):
    # print("ping: ",url,threading.current_thread())
    print('阻塞函数开始运行，当前的线程是：',url,threading.current_thread().name,threading.current_thread().ident,os.getpid())
    time.sleep(2)
    os.system("ping -c3 %s"%url)
    print('阻塞函数运行结束',threading.current_thread().name,threading.current_thread().ident,os.getpid())


def main_1():
    # 执行任务并且设置回调函数
    print("In main thred ", threading.current_thread().name,threading.current_thread().ident,os.getpid())
    loop = asyncio.get_event_loop()
    task = loop.create_task(func1())
    task.add_done_callback(callbackfunc)
    loop.run_until_complete(task)
    print("task result is ", task.result())


def main_2():
    # 执行任务并且设置回调函数，且不停止loop
    print("In main thred ", threading.current_thread().name,threading.current_thread().ident,os.getpid())
    loop = asyncio.get_event_loop()
    task = loop.create_task(func1())
    task.add_done_callback(callbackfunc)
    loop.run_forever()
    print("task result is ", task.result())


def main_2_1():
    # 执行任务并且设置回调函数，在回调函数中中止loop
    print("In main thred ", threading.current_thread().name,threading.current_thread().ident,os.getpid())
    loop = asyncio.get_event_loop()
    task = loop.create_task(func1())
    task.add_done_callback(callbackfunc2)
    loop.run_forever()
    print("task result is ", task.result())


def main_3():
    # 并行执行任务
    print("In main thred ", threading.current_thread().name,threading.current_thread().ident,os.getpid())
    loop = asyncio.get_event_loop()
    task1=loop.create_task(func1())
    task1.add_done_callback(callbackfunc)
    task2=loop.create_task(func2())
    task2.add_done_callback(callbackfunc)
    loop.run_forever()


async def main_3_1():
    # 使用asyncio.gather并行执行函数
    # asyncio.gather 返回的是所有已完成 Task 的 result，不需要再进行调用或其他操作，就可以得到全部结果
    print("In main thred ", threading.current_thread().name,threading.current_thread().ident,os.getpid())
    result=await asyncio.gather(func1(),func2())
    print(result)

async def main_3_11():
    # 使用asyncion.wait并行执行函数
    # asyncio.wait 使用一个set保存它创建的Task实例，因为set是无序的所以这也就是我们的任务不是顺序执行的原因。
    # 会返回两个值：done 和 pending，done 为已完成的协程 Task，
    # pending 为超时未完成的协程 Task，需通过 future.result 调用 Task 的 result
    print("In main thred ", threading.current_thread().name, threading.current_thread().ident, os.getpid())
    done, pending = await asyncio.wait([func1(),func2()], timeout=None)
    for done_task in done:
        print((f"{done_task.result()}"))

async def main_3_12():
    # 使用asyncio.gather并行执行函数,任务列表形式,调用gather时需要加"*"
    # asyncio.gather 返回的是所有已完成 Task 的 result，不需要再进行调用或其他操作，就可以得到全部结果
    print("In main thred ", threading.current_thread().name,threading.current_thread().ident,os.getpid())
    task_list=[]
    task1=asyncio.create_task(func1())
    task2=asyncio.create_task(func2())
    task_list.append(task1)
    task_list.append(task2)
    result=await asyncio.gather(*task_list)
    print(result)


def main_3_2():
    # 同步调用异步方法一：使用loop.run_until_complete调用main_3_1()
    print("In main thred ", threading.current_thread().name,threading.current_thread().ident,os.getpid())
    loop=asyncio.get_event_loop()
    loop.run_until_complete(main_3_1())
    loop.close()

def main_3_21():
    # 同步调异步方法一简化版：使用async.run减少代码
    print("In main thred ", threading.current_thread().name,threading.current_thread().ident,os.getpid())
    asyncio.run(main_3_1())
    print('asyncio.run called')

def main_3_3():
    # 同步调用异步方法二：使用asyncio.ensure_future调用 main_3_1()
    print("In main thred ", threading.current_thread().name,threading.current_thread().ident,os.getpid())
    loop=asyncio.get_event_loop()
    task=asyncio.ensure_future(main_3_1())
    loop.run_forever()


def start_thread_loop(loop):
    # 定义一个跑事件循环的线程函数
    print("start_thread_loop ", threading.current_thread().name,threading.current_thread().ident,os.getpid())
    asyncio.set_event_loop(loop)
    loop.run_forever()


def main_4():
    # 在子线程中运行事件循环，且执行同步函数,效果为顺序执行
    print("In main thread ", threading.current_thread().name,threading.current_thread().ident,os.getpid())
    loop=asyncio.get_event_loop()
    # 在子线程中运行事件循环，且run_forever
    t=threading.Thread(target=start_thread_loop,args=(loop,))
    t.start()
    # 在主线程中动态添加同步函数
    # loop.call_soon_threadsafe()没有阻塞主线程的运行，但是由于需要跑的函数ping是阻塞式函数，所以调用了三次，
    # 这三次结果是顺序执行的，并没有实现并发。
    loop.call_soon_threadsafe(ping,"www.baidu.com")
    loop.call_soon_threadsafe(ping, "www.qq.com")
    loop.call_soon_threadsafe(ping, "www.alibaba.com")
    print("主线程不会阻塞",threading.current_thread().name,threading.current_thread().ident,os.getpid())


def main_5():
    print("In main thread ", threading.current_thread().name,threading.current_thread().ident,os.getpid())
    loop = asyncio.get_event_loop()
    # 在子线程中运行事件循环，且run_forever,以下这两行在本函数中没起到作用
    t = threading.Thread(target=start_thread_loop, args=(loop,))
    t.start()
    # 在主线程中动态添加同步函数,虽然实现了并发，但是却是多线程执行的
    loop.run_in_executor(None,ping,"www.baidu.com")
    loop.run_in_executor(None,ping, "www.qq.com")
    loop.run_in_executor(None,ping, "www.alibaba.com")
    print("主线程不会阻塞",threading.current_thread().name,threading.current_thread().ident,os.getpid())


def main_6():
    print("In main thread ", threading.current_thread().name, threading.current_thread().ident,os.getpid())
    loop = asyncio.get_event_loop()
    # 在子线程中运行事件循环，且run_forever,以下这两行在本函数中没起到作用
    t = threading.Thread(target=start_thread_loop, args=(loop,))
    t.start()
    thread_executor=concurrent.futures.ThreadPoolExecutor(2)
    process_executor=concurrent.futures.ProcessPoolExecutor()
    # run_in_executor的第一个参数是执行器，这里执行器是使用concurrent.futures下的两个类，
    # 一个是thread一个是process，也就是执行器可以分为线程执行器和进程执行器。
    # 它们在初始化的时候都有一个max_workers参数，如果不传则根据系统自身决定
    loop.run_in_executor(process_executor, ping, "www.baidu.com")
    loop.run_in_executor(process_executor, ping, "www.qq.com")
    loop.run_in_executor(process_executor, ping, "www.alibaba.com")
    print("主线程不会阻塞", threading.current_thread().name, threading.current_thread().ident,os.getpid())


def main_6_1():
    print("In main thread ", threading.current_thread().name, threading.current_thread().ident,os.getpid())
    loop = asyncio.get_event_loop()
    # 在子线程中运行事件循环，且run_forever,以下这两行在本函数中没起到作用
    t = threading.Thread(target=start_thread_loop, args=(loop,))
    t.start()
    thread_executor=concurrent.futures.ThreadPoolExecutor(2)
    process_executor=concurrent.futures.ProcessPoolExecutor()
    # run_in_executor的第一个参数是执行器，这里执行器是使用concurrent.futures下的两个类，
    # 一个是thread一个是process，也就是执行器可以分为线程执行器和进程执行器。
    # 它们在初始化的时候都有一个max_workers参数，如果不传则根据系统自身决定
    loop.run_in_executor(thread_executor, ping, "www.baidu.com")
    loop.run_in_executor(thread_executor, ping, "www.qq.com")
    loop.run_in_executor(thread_executor, ping, "www.alibaba.com")
    # 这里结果上看起来，使用run_in_executor和使用多进程和多线程其实意义是一样的，其实是有区别的
    print("主线程不会阻塞", threading.current_thread().name, threading.current_thread().ident,os.getpid())


def main_7():
    print("In main thread ", threading.current_thread().name, threading.current_thread().ident, os.getpid())
    loop = asyncio.get_event_loop()
    # 在子线程中运行事件循环，run_forever
    t = threading.Thread(target=start_thread_loop, args=(loop,))
    t.start()
    # 通过asyncio.run_coroutine_threadsafe在loop上绑定了四个协程函数
    # 主线程不会被阻塞，起的四个协程函数几乎同时返回的结果
    # 但是协程所在的线程和主线程不是同一个线程，因为此时事件循环loop是放到了另外的子线程中跑的，所以此时这四个协程放到事件循环的线程中运行的
    asyncio.run_coroutine_threadsafe(func1(), loop)
    asyncio.run_coroutine_threadsafe(func1(), loop)
    asyncio.run_coroutine_threadsafe(func2(), loop)
    asyncio.run_coroutine_threadsafe(func2(), loop)
    print("主线程不会阻塞", threading.current_thread().name, threading.current_thread().ident, os.getpid())


async def main_8(loop:asyncio.AbstractEventLoop):
    t1=time.perf_counter()
    # 使用loop.create_task 创建task对象，返回asyncio.tasks.Task对象
    task1=loop.create_task(func1())
    task2=loop.create_task(func2())
    # 使用asyncio.run_coroutine_threadsafe 返回 Future对象
    # 注意这个对象没有 __await__方法，所以不能对其使用 await,但是可以对它设置回调函数
    task3=asyncio.run_coroutine_threadsafe(func1(),loop)
    task4=asyncio.run_coroutine_threadsafe(func2(),loop)
    # 使用run_in_executor创建阻塞的任务，返回Future对象
    task5=loop.run_in_executor(None,ping,"www.baidu.com")
    task6=loop.run_in_executor(None,ping,"www.alibaba.com")
    task7=asyncio.ensure_future(func1())
    task8=asyncio.ensure_future(func2())
    task1.add_done_callback(callbackfunc())
    task2.add_done_callback(callbackfunc())
    task3.add_done_callback(callbackfunc())
    task4.add_done_callback(callbackfunc())
    task5.add_done_callback(callbackfunc())
    task6.add_done_callback(callbackfunc())
    task7.add_done_callback(callbackfunc())
    task8.add_done_callback(callbackfunc())
    result=await asyncio.gather(task1,task2,task3,task4,task5,task6,task7,task8)
    print(result)
    t2=time.perf_counter()
    print(f'一共用了{t2-t1}s时间',threading.current_thread().name, threading.current_thread().ident, os.getpid())


def main_8_1():
    print("In main thread ", threading.current_thread().name, threading.current_thread().ident, os.getpid())
    loop = asyncio.get_event_loop()
    loop2= asyncio.new_event_loop()
    # 在子线程中运行事件循环，run_forever
    t = threading.Thread(target=start_thread_loop, args=(loop,))
    t.start()
    asyncio.run_coroutine_threadsafe(main_8(loop),loop)

def main_9():
    print("In main thread ", threading.current_thread().name, threading.current_thread().ident, os.getpid())
    loop = asyncio.get_event_loop()
    # 在子线程中运行事件循环，run_forever
    t = threading.Thread(target=start_thread_loop, args=(loop,))
    t.start()
    # 通过asyncio.run_coroutine_threadsafe在loop上绑定了四个协程函数
    # 主线程不会被阻塞，起的四个协程函数几乎同时返回的结果
    # 但是协程所在的线程和主线程不是同一个线程，因为此时事件循环loop是放到了另外的子线程中跑的，所以此时这四个协程放到事件循环的线程中运行的
    task_list=[func1(),func1(),func2(),func2()]
    for task in task_list:
        asyncio.run_coroutine_threadsafe(task, loop)
    print("主线程不会阻塞", threading.current_thread().name, threading.current_thread().ident, os.getpid())

if __name__=="__main__":
    main_9()
    print("主线程-运行结束。",threading.current_thread().name,threading.current_thread().ident,os.getpid())