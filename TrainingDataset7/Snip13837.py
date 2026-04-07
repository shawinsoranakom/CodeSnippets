def assert_and_parse_html(self, html, user_msg, msg):
    try:
        dom = parse_html(html)
    except HTMLParseError as e:
        standardMsg = "%s\n%s" % (msg, e)
        self.fail(self._formatMessage(user_msg, standardMsg))
    return dom