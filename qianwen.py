#pip3 install playwright
#playwright install
import asyncio
import logging
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import sys,os,time,threading,queue


url = "https://bazinga.aliyun-inc.com/chat"
#url="https://qianwen.aliyun.com/"
__xpath_content = '//div[starts-with(@class,"answerItem--")][last()]//div[contains(@class,"markdown-body")]'
__xpath_check = '//div[starts-with(@class,"answerItem--")][last()]//div[starts-with(@class,"btn--")]' \
                    '/span[text()="重新生成"]'
__state=f"{os.path.dirname(os.path.abspath(__file__))}/auth/state_%s.json"
counter=0
__headless=True
__auths=[["dingtalk_fwjrtt", "do4best"]]
logger=logging.getLogger('chat.qianwen')

print('__state: ',__state)


async def async_qa(page,question):
    await page.get_by_role("textbox").fill(question)
    await page.get_by_role("textbox").press("Enter")

    logger.info('waitting for check-dom attached...')
    await page.wait_for_selector(__xpath_check, state='attached')
    logger.info('start get answer...')
    em_content = await page.query_selector(__xpath_content)
    answer = await em_content.inner_text()
    logger.info('got-answer:%s' % answer)
    return answer

async def async_qa_loop(page,question):
    while True:
        question = yield
        logger.info('got-question:%s' % question)
        t11 = time.perf_counter()
        try:
            answer = await async_qa(page, question)
        except TimeoutError as e:
            logger.info('发生异常：%s' % e)
        t21 = time.perf_counter()
        logger.info('ts-got_answer:%d' % ((t21 - t11) * 1000))
        yield answer

async def async_check_login(page):
    pass

async def async_chat_loop(acc, pwd):
    t0=time.perf_counter()
    #auth=__auths[0]
    #acc,pwd=auth[0],auth[1]
    print(os.getcwd())
    state=__state%acc
    logger.info('state-use:%s'%acc)
    authed = os.path.exists(state)
    headless=__headless
    if(not authed):
        headless=False
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=headless)
        if (authed):
            context=await browser.new_context(storage_state=state,ignore_https_errors=True)
        else:
            context=await browser.new_context(ignore_https_errors=True)
        page= await context.new_page()
        await page.goto(url)
        if(not authed):
            print('登陆态丢失，请先完成登陆后重试')
            await page.wait_for_url(url,wait_until="domcontentloaded")
            await context.storage_state(path=state)
        t1 = time.perf_counter()
        logger.info('ts-open:%d'%((t1-t0)*1000))
        while True:
            question=yield
            logger.info('got-question:%s'%question)
            t11 = time.perf_counter()
            try:
                answer=await async_qa(page,question)
            except TimeoutError as e:
                logger.info('发生异常：%s' %e)
            t21=time.perf_counter()
            logger.info('ts-got_answer:%d'%((t21-t11)*1000))
            yield answer
        await page.close()
        await context.close()
        await browser.close()
        t3=time.perf_counter()
        logger.info('ts-total:%d'%((t3-t0)*1000))
        #return answer

async def async_chat_quick_ask(question):
    acc, pwd = __auths[0]
    t0 = time.perf_counter()
    print(os.getcwd())
    state = __state % acc
    logger.info('state-use:%s' % acc)
    authed = os.path.exists(state)
    headless = __headless
    if (not authed):
        headless = False
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=headless)
        if (authed):
            context=await browser.new_context(storage_state=state,ignore_https_errors=True)
        else:
            context=await browser.new_context(ignore_https_errors=True)
        page= await context.new_page()
        await page.goto(url)
        if(not authed):
            print('登陆态丢失，请先完成登陆后重试')
            await page.wait_for_url(url,wait_until="domcontentloaded")
            await context.storage_state(path=state)
        answer=await async_qa(page,question)
        await page.close()
        await context.close()
        await browser.close()
    t1 = time.perf_counter()
    logger.info('chat-time-used(%s): %d ms for "%s"' % (acc,  (t1 - t0) * 1000, question))
    return answer

async def async_chat_queue_worker(acc, pwd, q_in, q_out):
    logger.info(f'chat work-thread start: {threading.current_thread().name} ...')
    g = async_chat_loop(acc, pwd)
    while True:
        try:
            question=q_in.get()
            #print("q_in.get:%s" % question)
            await anext(g)
            answer = await g.asend(question)
            q_out.put(answer)
        except Exception as e:
            logger.error(e)
            #asyncio.sleep(0.1)
            break
    # q_in.close()
    # q_out.close()
    logger.info(f'chat work-thread stop:{threading.current_thread().name}')

def async_chat_run(acc, pwd):
    q_in=queue.Queue()
    q_out=queue.Queue()
    def worker():
        c=async_chat_queue_worker(acc, pwd, q_in, q_out)
        asyncio.run(c)
    thrd=threading.Thread(target=worker,args=(),daemon=True,name=f'chat-qianwen-{acc}')
    logger.info(f'start-chat-thread:{thrd.name}')
    thrd.start()

    async def ask(q):
        #print("q_in.put:%s"%q)
        q_in.put(q)
        #print("q_out.get")
        return q_out.get()
    return thrd,ask

def async_chat_runs():
    runners=[]
    for acc,pwd in __auths:
        p,f= async_chat_run(acc, pwd)
        runners.append({"instance":p,"call":f,"name":p.name})
    runner_cnt=len(runners)
    logger.info('chat-threads-total:%d'%runner_cnt)
    semaphore = threading.Semaphore(runner_cnt)
    async def ask(question):
        t0 = time.perf_counter()
        semaphore.acquire()
        try:
            lock = threading.Lock()
            lock.acquire()
            global counter
            n=counter%runner_cnt
            chat=runners[n]
            counter = counter + 1
            lock.release()
            answer= await chat["call"](question)
            t1=time.perf_counter()
            logger.info('chat-time-used(%s | n=%d | counter=%d): %d ms for "%s"' % (chat['name'],n,counter,(t1 - t0) * 1000,question))
        finally:
            semaphore.release()
        return answer
    return ask


def sync_chat_loop():
    t0 = time.perf_counter()
    auth = __auths[0]
    acc, pwd = auth[0], auth[1]
    state = __state % acc
    logger.info('state-use:%s' % acc)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=__headless)
        if (os.path.exists(state)):
            context = browser.new_context(storage_state=state, ignore_https_errors=True)
        else:
            context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.goto(url)
        t1 = time.perf_counter()
        logger.info('ts-open:%d' % ((t1 - t0)*1000))
        page.wait_for_load_state("domcontentloaded")
        while True:
            question=yield
            logger.info('input-question:%s'%question)
            t11 = time.perf_counter()
            try:
                page.get_by_role("textbox").fill(question)
                page.get_by_role("textbox").press("Enter")

                logger.info('waitting for check-dom attached...')
                page.wait_for_selector(__xpath_check, state='attached')
                logger.info('start get answer...')
                em_content = page.query_selector(__xpath_content)
                answer = em_content.inner_text()
                logger.info('got-answer:%s' % answer)
            except TimeoutError as e:
                logger.info('发生异常：%s' % e)
            t21 = time.perf_counter()
            logger.info('ts-got_answer:%d' % ((t21 - t11) * 1000))
            yield answer
        page.close()
        context.close()
        browser.close()
        t3 = time.perf_counter()
        logger.info('ts-total:%d' % ((t3 - t0)*1000))
        #return answer

def sync_chat_quick_ask(question):
    g = sync_chat_loop()
    next(g)
    answer=g.send(question)
    g.close()
    return answer

#def sync_ask_handler(handler):
