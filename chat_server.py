#pip3 install sanic
#pip3 install sanic.ext

from sanic import Sanic,request,response
import json,sanic.log,asyncio,logging,qianwen_old2,queue,os

app= Sanic('mychat2')

@app.main_process_start
async def main_process_start(app):
    #app.shared_ctx.queue = queue.Queue()
    print("on main_process_start")

@app.main_process_ready
async def main_process_ready(app):
    print("on main_process_ready")

@app.after_server_start
async def after_server_start(app):
    print("on after_server_start")
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] [%(process)d] [%(thread)d] [%(levelname)s] [%(name)s] [%(processName)s/'
                               '%(funcName)s] %(message)s')
    qianwen.async_chat_runs()

@app.after_reload_trigger
async def after_reload_trigger(app):
    print("on after_reload_trigger")
    pass

@app.on_request
async def print_state(request: request.Request):
    print("on-request:%s" % request.url,request.app.m.name,request.app.m.pid,request.app.m.state)

@app.get("/")
async def index(request: request.Request):
    print("app ctx is:",app.ctx)
    print("app shared-ctx is:", app.shared_ctx)
    return response.text("hello,world!")


@app.route("/chatapi",methods =['POST','GET'])
async def chatapi(request: request.Request):
    req_body=request.body.decode("utf-8")
    logging.info("request-body:%s"%req_body)
    result={"success":True,"data":None,"error_msg":None}
    if(req_body is not None):
         data=json.loads(request.body.decode("utf-8"))
         question=data.get('question')
         answer= await qianwen.async_chat_quick_ask(question)
         result["data"]=answer
    return response.json(result)

if __name__ == '__main__':
    print("current work dir is :",os.getcwd())
    print('current file dir is: ',os.path.dirname(os.path.abspath(__file__)))
    #chat=asyncio.run(qianwen.async_chat_runs())
    #g=chat('hello')
    #asyncio.run(g)
    # g=chat("hello")
    # asyncio.run(g)
    #asyncio.run(qianwen.async_chat_quick_ask('hello'))
    app.run(host="127.0.0.1", port=8000,debug=False,auto_reload=True,access_log=False)
