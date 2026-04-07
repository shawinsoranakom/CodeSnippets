def live_server_url(cls):
        return "http://%s:%s" % (cls.external_host or cls.host, cls.server_thread.port)