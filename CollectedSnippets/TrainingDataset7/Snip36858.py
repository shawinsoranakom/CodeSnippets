def test_no_referer(self):
        """
        Referer header is strictly checked for POST over HTTPS. Trigger the
        exception by sending an incorrect referer.
        """
        response = self.client.post("/", headers={"x-forwarded-proto": "https"})
        self.assertContains(
            response,
            "You are seeing this message because this HTTPS site requires a "
            "“Referer header” to be sent by your web browser, but "
            "none was sent.",
            status_code=403,
        )
        self.assertContains(
            response,
            "If you have configured your browser to disable “Referer” "
            "headers, please re-enable them, at least for this site, or for "
            "HTTPS connections, or for “same-origin” requests.",
            status_code=403,
        )
        self.assertContains(
            response,
            "If you are using the &lt;meta name=&quot;referrer&quot; "
            "content=&quot;no-referrer&quot;&gt; tag or including the "
            "“Referrer-Policy: no-referrer” header, please remove them.",
            status_code=403,
        )