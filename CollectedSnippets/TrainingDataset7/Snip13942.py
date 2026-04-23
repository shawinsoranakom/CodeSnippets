def live_server_url(cls):
        return "http://%s:%s" % (cls.host, cls.server_thread.port)