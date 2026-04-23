def assertRedirects(
        self,
        response,
        expected_url,
        status_code=302,
        target_status_code=200,
        msg_prefix="",
        fetch_redirect_response=True,
    ):
        """
        Assert that a response redirected to a specific URL and that the
        redirect URL can be loaded.

        Won't work for external links since it uses the test client to do a
        request (use fetch_redirect_response=False to check such links without
        fetching them).
        """
        if msg_prefix:
            msg_prefix += ": "

        if hasattr(response, "redirect_chain"):
            # The request was a followed redirect
            self.assertTrue(
                response.redirect_chain,
                msg_prefix
                + (
                    "Response didn't redirect as expected: Response code was %d "
                    "(expected %d)"
                )
                % (response.status_code, status_code),
            )

            self.assertEqual(
                response.redirect_chain[0][1],
                status_code,
                msg_prefix
                + (
                    "Initial response didn't redirect as expected: Response code was "
                    "%d (expected %d)"
                )
                % (response.redirect_chain[0][1], status_code),
            )

            url, status_code = response.redirect_chain[-1]

            self.assertEqual(
                response.status_code,
                target_status_code,
                msg_prefix
                + (
                    "Response didn't redirect as expected: Final Response code was %d "
                    "(expected %d)"
                )
                % (response.status_code, target_status_code),
            )

        else:
            # Not a followed redirect
            self.assertEqual(
                response.status_code,
                status_code,
                msg_prefix
                + (
                    "Response didn't redirect as expected: Response code was %d "
                    "(expected %d)"
                )
                % (response.status_code, status_code),
            )

            url = response.url
            scheme, netloc, path, query, fragment = urlsplit(url)

            # Prepend the request path to handle relative path redirects.
            if not path.startswith("/"):
                url = urljoin(response.request["PATH_INFO"], url)
                path = urljoin(response.request["PATH_INFO"], path)

            if fetch_redirect_response:
                # netloc might be empty, or in cases where Django tests the
                # HTTP scheme, the convention is for netloc to be 'testserver'.
                # Trust both as "internal" URLs here.
                domain, port = split_domain_port(netloc)
                if domain and not validate_host(domain, settings.ALLOWED_HOSTS):
                    raise ValueError(
                        "The test client is unable to fetch remote URLs (got %s). "
                        "If the host is served by Django, add '%s' to ALLOWED_HOSTS. "
                        "Otherwise, use "
                        "assertRedirects(..., fetch_redirect_response=False)."
                        % (url, domain)
                    )
                # Get the redirection page, using the same client that was used
                # to obtain the original response.
                extra = response.client.extra or {}
                headers = response.client.headers or {}
                redirect_response = response.client.get(
                    path,
                    QueryDict(query),
                    secure=(scheme == "https"),
                    headers=headers,
                    **extra,
                )
                self.assertEqual(
                    redirect_response.status_code,
                    target_status_code,
                    msg_prefix
                    + (
                        "Couldn't retrieve redirection page '%s': response code was %d "
                        "(expected %d)"
                    )
                    % (path, redirect_response.status_code, target_status_code),
                )

        self.assertURLEqual(
            url,
            expected_url,
            msg_prefix
            + "Response redirected to '%s', expected '%s'" % (url, expected_url),
        )