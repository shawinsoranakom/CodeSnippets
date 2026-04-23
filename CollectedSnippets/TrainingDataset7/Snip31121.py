def test_get_host_suggestion_of_allowed_host(self):
        """
        get_host() makes helpful suggestions if a valid-looking host is not in
        ALLOWED_HOSTS.
        """
        msg_invalid_host = "Invalid HTTP_HOST header: %r."
        msg_suggestion = msg_invalid_host + " You may need to add %r to ALLOWED_HOSTS."
        msg_suggestion2 = (
            msg_invalid_host
            + " The domain name provided is not valid according to RFC 1034/1035"
        )

        for host in [  # Valid-looking hosts
            "example.com",
            "12.34.56.78",
            "[2001:19f0:feee::dead:beef:cafe]",
            "xn--4ca9at.com",  # Punycode for öäü.com
        ]:
            request = HttpRequest()
            request.META = {"HTTP_HOST": host}
            with self.assertRaisesMessage(
                DisallowedHost, msg_suggestion % (host, host)
            ):
                request.get_host()

        for domain, port in [  # Valid-looking hosts with a port number
            ("example.com", 80),
            ("12.34.56.78", 443),
            ("[2001:19f0:feee::dead:beef:cafe]", 8080),
        ]:
            host = "%s:%s" % (domain, port)
            request = HttpRequest()
            request.META = {"HTTP_HOST": host}
            with self.assertRaisesMessage(
                DisallowedHost, msg_suggestion % (host, domain)
            ):
                request.get_host()

        for host in self.poisoned_hosts:
            request = HttpRequest()
            request.META = {"HTTP_HOST": host}
            with self.assertRaisesMessage(DisallowedHost, msg_invalid_host % host):
                request.get_host()

        request = HttpRequest()
        request.META = {"HTTP_HOST": "invalid_hostname.com"}
        with self.assertRaisesMessage(
            DisallowedHost, msg_suggestion2 % "invalid_hostname.com"
        ):
            request.get_host()