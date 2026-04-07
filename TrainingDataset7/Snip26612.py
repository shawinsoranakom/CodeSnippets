def test_custom_request_checker(self):
        class SubclassedMiddleware(BrokenLinkEmailsMiddleware):
            ignored_user_agent_patterns = (
                re.compile(r"Spider.*"),
                re.compile(r"Robot.*"),
            )

            def is_ignorable_request(self, request, uri, domain, referer):
                """Check user-agent in addition to normal checks."""
                if super().is_ignorable_request(request, uri, domain, referer):
                    return True
                user_agent = request.META["HTTP_USER_AGENT"]
                return any(
                    pattern.search(user_agent)
                    for pattern in self.ignored_user_agent_patterns
                )

        self.req.META["HTTP_REFERER"] = "/another/url/"
        self.req.META["HTTP_USER_AGENT"] = "Spider machine 3.4"
        SubclassedMiddleware(self.get_response)(self.req)
        self.assertEqual(len(mail.outbox), 0)
        self.req.META["HTTP_USER_AGENT"] = "My user agent"
        SubclassedMiddleware(self.get_response)(self.req)
        self.assertEqual(len(mail.outbox), 1)