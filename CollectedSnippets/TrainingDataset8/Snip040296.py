def get_app(self):
        self._cache = ForwardMsgCache()
        return tornado.web.Application(
            [(r"/message", MessageCacheHandler, dict(cache=self._cache))]
        )