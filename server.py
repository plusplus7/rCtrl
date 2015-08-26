#-*- coding: UTF-8 -*-
import tornado.web
import tornado.websocket
import json
import uuid
import tornado.ioloop
import os

g_machines = {}
g_commanders = {}

def JsonResponser(code, result, msg):
    response = {}
    response['code']   = code
    response['result'] = result
    response['msg']    = msg
    return json.dumps(response)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", machines = g_machines)

class ImageHandler(tornado.web.RequestHandler):
    def get(self, machine_id = "test_machine"):
        self.render("image.html", machine_id = machine_id)

    def post(self, machine_id):
        static_path = os.path.join(os.path.dirname(__file__), 'static')
        file_path = os.path.join(static_path, machine_id + ".png")

        file_metas = self.request.files['image']
        for meta in file_metas:
            with open(file_path, 'wb') as fp:
                fp.write(meta['body'])
        self.finish(JsonResponser(200, None, 'Success'))

class CommandHandler(tornado.web.RequestHandler):
    def get(self, machine_id):
        if machine_id not in g_machines.keys():
            self.finish(JsonResponser(404, None, "Machine_id not exist!"))
        else:
            self.finish(JsonResponser(200, g_machines[machine_id]["command"], ""))
            g_machines[machine_id]["command"] = []

class MachineStatusHandler(tornado.web.RequestHandler):
    def post(self, machine_id):
        status = self.get_argument("status")
        if cmp(status, "On") == 0:
            g_machines[machine_id] = {}
            g_machines[machine_id]['command'] = []
            g_machines[machine_id]['status'] = "On"
            ControlCenterHandler.announcement("Join", "Bot_" + machine_id)
        elif cmp(status, "Off") == 0 and machine_id in g_machines.keys():
            ControlCenterHandler.announcement("Left", "Bot_" + machine_id)
            g_machines.pop(machine_id)
        elif cmp(status, "Off") == 0 and machine_id not in g_machines.keys():
            self.finish(JsonResponser(404, None, "Machine_id not exist!"))
        else:
            self.finish(JsonResponser(400, None, "Not valid status(On/Off)"))
        self.finish(JsonResponser(200, None, "finished"))

    def get(self, machine_id = None):
        self.write(JsonResponser(200, g_machines, ""))

def MessageParser(mode, message):
    j_msg = {}
    j_msg["Mode"] = mode 
    j_msg["Msg"] = message
    return json.dumps(j_msg)

def MessageParser3(from_, message):
    j_msg = {}
    j_msg["From"] = from_
    j_msg["Msg"] = message
    return json.dumps(j_msg)

class ControlCenterHandler(tornado.websocket.WebSocketHandler):

    @staticmethod
    def announcement(mode, msg):
        for i in g_commanders.keys():
            g_commanders[i].send_message(mode, msg)

    def send_message(self, mode, message):
        try:
            self.write_message(MessageParser(mode, message))
        except:
            pass

    def open(self):
        self.me_id = str(uuid.uuid4())[0:8]
        self.send_message("System", '欢迎来到rCtrl控制中心<br/>您的ID是%s' % self.me_id)
        self.send_message("Online", json.dumps(g_commanders.keys()))
        g_commanders[self.me_id] = self
        ControlCenterHandler.announcement("Join", self.me_id)

    def on_close(self):
        g_commanders.pop(self.me_id)
        ControlCenterHandler.announcement("Left", self.me_id)

    def on_message(self, message):
        j_msg = None
        try:
            j_msg = json.loads(message)
            if "Recipient" not in j_msg or "Message" not in j_msg:
                return
        except Exception as e:
            print e
            return

        if cmp(j_msg["Recipient"], "all") == 0:
            ControlCenterHandler.announcement("Speak", MessageParser3(self.me_id, j_msg["Message"]))
            return

        if j_msg["Recipient"] in g_commanders.keys():
            g_commanders[j_msg["Recipient"]].send_message("Message", MessageParser3(self.me_id, j_msg["Message"]))
            return

        if j_msg["Recipient"] in g_machines.keys():
            g_machines[j_msg["Recipient"]]["command"].append(j_msg["Message"])
            self.send_message("System", 'Command bot %s successfully' % j_msg["Recipient"])
            return
        self.send_message("System", "发送失败")

urls = [
    (r'/', IndexHandler),
    (r'/machine', MachineStatusHandler),
    (r'/machine/(?P<machine_id>[a-zA-Z0-9-_]+).stat', MachineStatusHandler),
    (r'/image/(?P<machine_id>[a-zA-Z0-9-_]+).png', ImageHandler),
    (r'/command/(?P<machine_id>[a-zA-Z0-9-_]+).list', CommandHandler),
    (r'/controlcenter', ControlCenterHandler),
]

settings = {
    "static_path"   : os.path.join(os.path.dirname(__file__), "static"),
    "template_path" : os.path.join(os.path.dirname(__file__), "templates"),
    "debug"         : True,
    "gzip"          : True,
}

def main(host="0.0.0.0", port=7070):
    app = tornado.web.Application(urls, **settings)
    app.listen(port, host)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
