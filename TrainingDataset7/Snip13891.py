def assertNotInHTML(self, needle, haystack, msg_prefix=""):
        self.assertInHTML(needle, haystack, count=0, msg_prefix=msg_prefix)