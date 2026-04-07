def _get_raw_host(self):
        """
        Return the HTTP host using the environment or request headers. Skip
        allowed hosts protection, so may return an insecure host.
        """
        # We try three options, in order of decreasing preference.
        if settings.USE_X_FORWARDED_HOST and ("HTTP_X_FORWARDED_HOST" in self.META):
            host = self.META["HTTP_X_FORWARDED_HOST"]
        elif "HTTP_HOST" in self.META:
            host = self.META["HTTP_HOST"]
        else:
            # Reconstruct the host using the algorithm from PEP 333.
            host = self.META["SERVER_NAME"]
            server_port = self.get_port()
            if server_port != ("443" if self.is_secure() else "80"):
                host = "%s:%s" % (host, server_port)
        return host