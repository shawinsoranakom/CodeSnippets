def setUp(self):
        self.base_url = "%s://%s" % (self.protocol, self.domain)
        cache.clear()