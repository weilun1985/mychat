import asyncio,logging,os,time,multiprocessing
from typing import Coroutine
from playwright.async_api import async_playwright,Page,Browser,Frame,Locator,ElementHandle

#url = "https://bazinga.aliyun-inc.com/chat"
url="https://qianwen.aliyun.com/"
logger=logging.getLogger('chat.qianwen')

__xpath_content = '//div[starts-with(@class,"answerItem--")][last()]//div[contains(@class,"markdown-body")]'
__xpath_check = '//div[starts-with(@class,"answerItem--")][last()]//div[starts-with(@class,"btn--")]' \
                    '/span[text()="重新生成"]'
__root_dir=os.path.dirname(os.path.abspath(__file__))
__state_dir=f"{__root_dir}/auth"
__state=f"{__state_dir}/state_%s.json"

__auths=[["dingtalk_fwjrtt", "do4best"]]
__counter=0
__headless=False



logger.info(f'chat-root-dir: {__root_dir}')
logger.info(f'chat-state-dir: {__state_dir}')

# 判断权限目录是否存在，不存在则创建
if not os.path.exists(__state_dir):
    os.makedirs(__state_dir)


async def screenshot(acc,page:Page):
    path_screenshot = f'{__state_dir}/scst_{acc}.png'
    logger.info(f'auth screenshot and save:{url}')
    await page.screenshot(path=path_screenshot)

def get_state_path(acc,pwd):
    path = __state % acc
    exist=os.path.exists(path)
    return path,exist


async def auto_auth_1(acc,page:Page):
    xpath_input = '//div[@role="textbox" and @class="tts-editor-content"]'
    in_txb = await page.query_selector(xpath_input)
    if in_txb is None:
        logger.info(f'登陆态丢失，请先完成登陆后重试:{url}')
        xpath_btn1 = '//div[@class="method-btn"]/i[contains(@class,"next-icon-scan")]/parent::div'
        xpath_qrcode = '//div[@class="qrcode-img"]/img[@class="qr-image"]'
        xpath_btn2 = '//button[contains(@class,"next-btn-primary")]'
        btn1=await page.query_selector(xpath_btn1)
        await btn1.click()
        qrcode = await page.query_selector(xpath_qrcode)
        if qrcode is None:
            await page.wait_for_selector(xpath_qrcode)
            await page.wait_for_load_state("load")
        await screenshot(acc,page)
        btn_2=await page.wait_for_selector(xpath_btn2)
        await btn_2.click()
        if not page.url.startswith(url):
            # 未登陆且发生URL重定向,等待登陆成功后URL重定向到目标页面
            await page.wait_for_url(url, wait_until="domcontentloaded")
        in_txb = await page.query_selector(xpath_input)
    return in_txb


async def auto_auth_2(acc,page:Page):
    xpath_input = '//textarea[@id="primary-textarea"]'
    in_txb =await page.query_selector(xpath_input)
    if in_txb is None:
        logger.info(f'登陆态丢失，请先完成登陆后重试:{url}')
        xpath_btn1='//button/span[text()="立即使用"]/parent::button'
        xpath_loginframe='//iframe[@id="aliyun-login-box"]'
        xpath_qrcode='//img[@class="alipay-qrcode"]'
        btn1 = await page.query_selector(xpath_btn1)
        await btn1.click()
        frame=page.frame_locator(xpath_loginframe)
        qrcode=frame.locator(xpath_qrcode)
        await qrcode.wait_for(state= "visible")
        await screenshot(acc, page)
        in_txb=await page.wait_for_selector(xpath_input,state="visible")
        #await in_txb.wait_for(state= "visible")
    return in_txb


# 判断登陆状态且获取输入框
async def chat_checkout_input(acc,pwd,page:Page):
    if page.url.startswith("https://qianwen."):
        in_txb= await auto_auth_2(acc,page)
    else:
        in_txb= await auto_auth_1(acc,page)
    state, exist = get_state_path(acc, pwd)
    if in_txb is not None:
        await page.context.storage_state(path=state)
        logger.info(f'登陆状态已保存:{url},{state}')
    else:
        # 没有能成功登陆，抛出异常,并清除状态文件
        await chat_state_clear(state)
        logger.error(f"未能取到输入框：{url}")
        raise Exception(f'未成功登陆状态，请下次运行重试登陆:{url},{acc}')
    return in_txb

# 提问及结果获取函数
async def chat_qa_once(intxb:Locator|ElementHandle,page:Page, question):
    await intxb.fill(question)
    await intxb.press("Enter")

    logger.info('input-question-length: %d,waitting for check-dom attached...'%len(question))
    # 等待答案超时时间5分钟
    await page.wait_for_selector(__xpath_check, state='attached',timeout=60000*5)
    logger.info('start get answer...')
    em_content = await page.query_selector(__xpath_content)
    answer = await em_content.inner_text()
    answer=answer.replace('\n\n\n','\n').replace('\n\n','\n')
    logger.info('got-answer-length: %d' % len(answer))
    return answer


# 清除登陆状态
async def chat_state_clear(state):
    os.remove(state)

# 机器人运行模版函数,返回具体执行函数
async def chat_core(acc,pwd,browser:Browser,handler: Coroutine):
    t0 = time.perf_counter()
    # 未打开页面，检测历史登陆状态
    state,exists =get_state_path(acc,pwd)
    if (exists):
        context = await browser.new_context(storage_state=state, ignore_https_errors=True)
    else:
        context = await browser.new_context(ignore_https_errors=True)
    page = await context.new_page()
    await page.goto(url,timeout=600000,wait_until="domcontentloaded")
    # 打开页面后，再次检测页面登陆状态
    in_txb=await chat_checkout_input(acc,pwd,page)
    t1 = time.perf_counter()
    logger.info(f'chat-core-opend: [{acc}] time-used={(t1 - t0) * 1000} state={state}')
    result=None
    if handler is not None:
        result= await handler(in_txb,page)

    await page.close()
    await context.close()
    t3 = time.perf_counter()
    logger.info(f'chat-core-closed: [{acc}] time-keep={(t3 - t0) * 1000} state={state}')
    return result

# 单次模式，每次问答都会启动一次内核
async def chat_once(question):
    t0 = time.perf_counter()
    acc,pwd='default','None'
    async def once_handler(intxb,page):
        answer =await chat_qa_once(intxb,page,question)
        return answer
    handler=once_handler
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=__headless)
        result=await chat_core(acc=acc,pwd=pwd,browser=browser,handler=handler)
    t1 = time.perf_counter()
    logger.info(f'chat-qa-timeused: [{acc}] time-used={(t1 - t0) * 1000} \r\nquestion={question}\r\nanswer={result}')
    return result


async def chat_loop():
    acc, pwd = 'default', 'None'
    in_queue=asyncio.Queue()
    out_queue=asyncio.Queue()
    async def loop_handler(intxb,page):
        while True:
            question=await in_queue.get()
            answer =await chat_qa_once(intxb,page,question)
            await out_queue.put(answer)
    async def func(question):
        await in_queue.put(question)
        result=await out_queue.get()
        return result

    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=__headless)
        await chat_core(acc=acc,pwd=pwd,browser=browser,handler=loop_handler)
        logger.info(f"chat-loop-start:{url},{acc}")

    return func

def chat_loop_start():
    in_q = multiprocessing.Queue()
    out_q = multiprocessing.Queue()
    async def worker_item():
        func=await chat_loop()



