import asyncio,logging,os,time
from typing import Coroutine
from playwright.async_api import async_playwright,Page,Browser

#url = "https://bazinga.aliyun-inc.com/chat"
url="https://qianwen.aliyun.com/"
logger=logging.getLogger('chat.qianwen')

__xpath_input='//div[@role="textbox" and @class="tts-editor-content"]'
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


async def auto_auth(acc,page:Page):
    if page.url.startswith("https://qianwen."):
        await auto_auth_2(acc,page)
    else:
        await auto_auth_1(acc,page)

async def screenshot(acc,page:Page):
    path_screenshot = f'{__state_dir}/scst_{acc}.png'
    await page.screenshot(path=path_screenshot)

async def auto_auth_1(acc,page:Page):
    xpath_btn1='//div[@class="method-btn"]/i[contains(@class,"next-icon-scan")]/parent::div'
    xpath_qrcode='//div[@class="qrcode-img"]/img[@class="qr-image"]'
    xpath_btn2='//button[contains(@class,"next-btn-primary")]'
    btn1=await page.query_selector(xpath_btn1)
    await btn1.click()
    await page.wait_for_selector(xpath_qrcode)
    await page.wait_for_load_state("load")
    await screenshot(acc,page)
    btn_2=await page.wait_for_selector(xpath_btn2)
    await btn_2.click()
    await page.wait_for_load_state("domcontentloaded")

async def auto_auth_2(acc,page:Page):
    xpath_btn1='//button/span[text()="立即使用"]/parent::button'
    xpath_qrcode='//img[@class="alipay-qrcode"]'
    btn1 = await page.query_selector(xpath_btn1)
    await btn1.click()
    await page.wait_for_selector(xpath_qrcode)
    await page.wait_for_load_state("load")
    await screenshot(acc, page)


# 提问及结果获取函数
async def chat_qa_once(page:Page, question):
    await page.get_by_role("textbox").fill(question)
    await page.get_by_role("textbox").press("Enter")

    logger.info('input-question-length: %d,waitting for check-dom attached...'%len(question))
    # 等待答案超时时间5分钟
    await page.wait_for_selector(__xpath_check, state='attached',timeout=60000*5)
    logger.info('start get answer...')
    em_content = await page.query_selector(__xpath_content)
    answer = await em_content.inner_text()
    answer=answer.replace('\n\n\n','\n').replace('\n\n','\n')
    logger.info('got-answer-length: %d' % len(answer))
    return answer

# 登陆验证函数
async def chat_check_authed(acc, pwd, page:Page):
    state = __state % acc
    # 如果没有打开任何页面，有state文件就暂判定已登陆，无则判定未登陆。
    if page is None:
        if not os.path.exists(state):
            return False,state
        else:
            return True,state
    # # 如果已经打开有页面，无state就判定未登陆，有则继续根据页面元素判定登陆状态。
    # if not os.path.exists(state):
    #     return False,state
    # 已经打开了页面，通过页面元素判断是否已登陆
    context = page.context
    in_txb = await page.query_selector(__xpath_input)
    # 已登陆,不做任何处理，返回True
    if in_txb is not None:
        # state文件不存在，则保存state
        if not os.path.exists(state):
            await context.storage_state(path=state)
        return True,state

    logger.info('登陆态丢失，请先完成登陆后重试')
    await auto_auth(acc,page)
    # 先通过await timeout 来留出人工操作的时间
    try:
        if not page.url.startswith(url):
            # 未登陆且发生URL重定向,等待登陆成功后URL重定向到目标页面
            await page.wait_for_url(url, wait_until="domcontentloaded")
        else:
            # 未登陆且URL没有发生重定向，则等待指定元素出现
            in_txb=await page.wait_for_selector(__xpath_input)
    except TimeoutError as e:
        logger.error("登陆失败：操作超时!")
        return False,state
    # 再次判断登陆状态
    if in_txb is None:
        in_txb = await page.query_selector(__xpath_input)
    if in_txb is not None:
        # 保存登陆cookie
        await context.storage_state(path=state)
        logger.info('登陆成功，登陆状态已保存')
        return True,state
    else:
        logger.warning('登陆失败。')
        return False,state

# 清除登陆状态
async def chat_state_clear(state):
    os.remove(state)

# 机器人运行模版函数,返回具体执行函数
async def chat_core(acc,pwd,browser:Browser,handler: Coroutine):
    t0 = time.perf_counter()
    # 未打开页面，检测历史登陆状态
    authed, state =await chat_check_authed(acc, pwd, None)
    if (authed):
        context = await browser.new_context(storage_state=state, ignore_https_errors=True)
    else:
        context = await browser.new_context(ignore_https_errors=True)

    page = await context.new_page()
    await page.goto(url)
    await page.wait_for_load_state("domcontentloaded")
    # 打开页面后，再次检测页面登陆状态
    authed, state =await chat_check_authed(acc, pwd, page)
    if not authed:
        # 没有能成功登陆，抛出异常,并清除状态文件
        chat_state_clear(state)
        logger.info(f'chat-core-auth_failed: [{acc}]')
        raise Exception('未成功登陆状态，请下次运行重试登陆')

    t1 = time.perf_counter()
    logger.info(f'chat-core-opend: [{acc}] time-used={(t1 - t0) * 1000} state={state}')
    result=None
    if handler is not None:
        result= await handler(page)

    await page.close()
    await context.close()
    t3 = time.perf_counter()
    logger.info(f'chat-core-closed: [{acc}] time-keep={(t3 - t0) * 1000} state={state}')
    return result

# 单次模式，每次问答都会启动一次内核
async def chat_once(question):
    t0 = time.perf_counter()
    acc,pwd='default','None'
    async def once_handler(page):
        answer =await chat_qa_once(page,question)
        return answer
    handler=once_handler
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=__headless)
        result=await chat_core(acc=acc,pwd=pwd,browser=browser,handler=handler)
    t1 = time.perf_counter()
    logger.info(f'chat-qa-timeused: [{acc}] time-used={(t1 - t0) * 1000} \r\nquestion={question}\r\nanswer={result}')
    return result


