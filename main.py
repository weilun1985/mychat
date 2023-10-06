import logging
import chat_qianwen
import threading,os
import asyncio

logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] [%(process)d] [%(thread)d] [%(levelname)s] [%(name)s] [%(processName)s/'
                               '%(funcName)s] %(message)s')


# 单次模式测试，循环测试
def test1():
    while True:
        question=input('\r\n请输入问题：（输入n表示退出）')
        if question == 'n':
            break
        print("问题：",question)
        answer=asyncio.run(chat_qianwen.chat_once(question))
        print("回答：",answer)
    input('请输入任意键退出')


if __name__ == '__main__':
    print("主线程-启动运行 ", threading.current_thread().name, threading.current_thread().ident, os.getpid())
    test1()
    print("主线程-运行结束。",threading.current_thread().name,threading.current_thread().ident,os.getpid())
