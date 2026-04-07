def process_response(self, request, response):
        """Send broken link emails for relevant 404 NOT FOUND responses."""
        if response.status_code == 404 and not settings.DEBUG:
            domain = request.get_host()
            path = request.get_full_path()
            referer = request.META.get("HTTP_REFERER", "")

            if not self.is_ignorable_request(request, path, domain, referer):
                ua = request.META.get("HTTP_USER_AGENT", "<none>")
                ip = request.META.get("REMOTE_ADDR", "<none>")
                mail_managers(
                    "Broken %slink on %s"
                    % (
                        (
                            "INTERNAL "
                            if self.is_internal_request(domain, referer)
                            else ""
                        ),
                        domain,
                    ),
                    "Referrer: %s\nRequested URL: %s\nUser agent: %s\n"
                    "IP address: %s\n" % (referer, path, ua, ip),
                    fail_silently=True,
                )
        return response