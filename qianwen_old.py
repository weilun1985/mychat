import sys,time,os,logging
from playwright.sync_api import Playwright,sync_playwright,TimeoutError

class Qianwen:
    #url="https://qianwen.aliyun.com/"
    url = "https://bazinga.aliyun-inc.com/chat"
    __xpath_content = '//div[starts-with(@class,"answerItem--")][last()]//div[contains(@class,"markdown-body")]'
    __xpath_check = '//div[starts-with(@class,"answerItem--")][last()]//div[starts-with(@class,"btn--")]' \
                    '/span[text()="重新生成"]'
    __logger = logging.getLogger("Qianwen")

    # def __new__(cls, *args, **kwargs):
    #     if not hasattr(cls,"_instance"):
    #         cls._instance = super().__new__(cls, *args, **kwargs)
    #     return cls._instance

    def __init__(self,acc,pwd):
        print("init qianwen")
        self.__acc=acc
        self.__pwd=pwd
        self.__state="auth/state_%s.json"%(acc)
        playwright=sync_playwright().start()
        self.__playwright=playwright
        self.__browser=self.__playwright.chromium.launch(headless=False)
        if (os.path.exists(self.__state)):
            self.__context=self.__browser.new_context(storage_state=self.__state,ignore_https_errors=True)
        else:
            self.__context = self.__browser.new_context(ignore_https_errors=True)
        self.__page=self.__context.new_page()
        self.check_login()
        pass

    def check_login(self):
        page = self.__page
        context=self.__context
        if not page.url.startswith(self.url):
            page.goto(self.url)
            page.wait_for_load_state("domcontentloaded")
        inpt=page.query_selector('[role="textbox"]')
        if inpt is None:
            return False
        context.storage_state(path=self.__state)
        return True


    def ask(self,question):
        logger = self.__logger
        page = self.__page
        xpath_check = self.__xpath_check
        xpath_content = self.__xpath_content
        result = {"question": question,"error":None}
        if self.check_login()==False:
            err_msg="登陆态丢失，请重新登陆或更新cookie文件:%s"%(self.__state)
            result["err_msg"]=err_msg
            logger.error(err_msg)
            return result
        logger.info('ask:%s'%question)
        page.get_by_role("textbox").fill(question)
        page.get_by_role("textbox").press("Enter")
        try:
            logger.info('waitting for check-dom attached...')
            page.wait_for_selector(xpath_check, state='attached')
            logger.info('start get answer...')
            answer = page.query_selector(xpath_content).inner_text()
            result["answer"]=answer
            logger.info('answer:%s'%answer)
        except TimeoutError as e:
            logger.error('发生异常：%s' %e)
            result["err_msg"]=e
        return result

    def close(self):
        if (self.__page != None):
            self.__page.close()
        if(self.__context!=None):
            self.__context.close()
        self.__playwright.stop()
        pass