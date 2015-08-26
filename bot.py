import thread
from optparse import OptionParser
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import urllib2
import urllib
import time
import json
import os
import sys
import platform

def screen_capture(filepath):
    systype = platform.system()
    if cmp(systype, "Darwin") == 0:
        os.system("screencapture -x " + filepath)
    elif cmp(systype, "Windows") == 0:
        pass
    else:
        print "HEHE: ", systype
        sys.exit(-1)
        pass

class ServerClient():
    def __init__(self, url):
        self.url = url

    def invoke_method_get(self, method):
        try:
            request = urllib2.Request(self.url + method)
            response = urllib2.urlopen(request)
            j_res = json.loads(response.read())
            return (True, j_res["code"], j_res["result"], j_res["msg"])
        except Exception as e:
            return (False, "Exception: " + str(e))

    def invoke_method_post(self, method, data, headers = {}):
        try:
            request = urllib2.Request(self.url + method, data, headers)
            response = urllib2.urlopen(request)
            j_res = json.loads(response.read())
            return (True, j_res["code"], j_res["result"], j_res["msg"])
        except Exception as e:
            return (False, "Exception: " + str(e))

    def post_image(self, filename):
        data, headers = multipart_encode({"image": open(filename)})
        return self.invoke_method_post("image/" + filename, data, headers)

    def post_status(self, machine_id, status):
        data = urllib.urlencode({"status" : status})
        return self.invoke_method_post("machine/" + machine_id + ".stat", data)

    def get_command(self, machine_id):
        return self.invoke_method_get("command/" + machine_id + ".list")

def screen_uploader(machine_id, url, sleeptime = 1):
    client = ServerClient(url)
    filename = machine_id + ".png"
    while True:
        screen_capture(filename)
        print client.post_image(filename)
        time.sleep(sleeptime)

def command_fetcher(machine_id, url, sleeptime):
    client = ServerClient(url)
    while True:
        print client.get_command(machine_id)
        time.sleep(sleeptime)

def get_parser():
    parser = OptionParser()
    parser.add_option("-m",
                      "--machine_id",
                      default = "test_machine",
                      dest = "machine_id",
                      help = "Machine ID")
    parser.add_option("-u",
                      "--url",
                      default = "http://localhost:7070/",
                      dest = "url",
                      help = "The url of service")
    parser.add_option("-t",
                      "--time",
                      default = 1,
                      dest = "time",
                      help = "Sleep time of upload interval")
    return parser

def main():
    p = get_parser()
    (options, args) = p.parse_args()
    client = ServerClient(options.url)

    # Regist machine_id on server
    print client.post_status("test_machine", "On")

    # Start uploading screen status
    thread.start_new_thread(screen_uploader, (options.machine_id, options.url, options.time))

    # Start fetching command
    thread.start_new_thread(command_fetcher, (options.machine_id, options.url, options.time))
    while True:
        time.sleep(100)
        pass

    # Start gossiping with clients

if __name__ == "__main__":
    register_openers()
    main()
