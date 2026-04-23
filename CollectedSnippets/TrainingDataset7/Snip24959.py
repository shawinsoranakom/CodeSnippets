def assertNotMsgId(self, msgid, s, use_quotes=True):
        if use_quotes:
            msgid = '"%s"' % msgid
        msgid = re.escape(msgid)
        return self.assertTrue(not re.search("^msgid %s" % msgid, s, re.MULTILINE))