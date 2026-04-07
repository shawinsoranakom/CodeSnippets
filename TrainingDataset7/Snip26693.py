def is_ignorable_request(self, request, uri, domain, referer):
                """Check user-agent in addition to normal checks."""
                if super().is_ignorable_request(request, uri, domain, referer):
                    return True
                user_agent = request.META["HTTP_USER_AGENT"]
                return any(
                    pattern.search(user_agent)
                    for pattern in self.ignored_user_agent_patterns
                )