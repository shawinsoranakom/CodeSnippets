def assertURLEqual(self, url1, url2, msg_prefix=""):
        """
        Assert that two URLs are equal despite the ordering
        of their querystring. Refs #22360.
        """
        parsed_url1 = urlsplit(url1)
        path1 = parsed_url1.path
        parsed_qs1 = dict(parse_qsl(parsed_url1.query))

        parsed_url2 = urlsplit(url2)
        path2 = parsed_url2.path
        parsed_qs2 = dict(parse_qsl(parsed_url2.query))

        for parsed_qs in [parsed_qs1, parsed_qs2]:
            if "_changelist_filters" in parsed_qs:
                changelist_filters = parsed_qs["_changelist_filters"]
                parsed_filters = dict(parse_qsl(changelist_filters))
                parsed_qs["_changelist_filters"] = parsed_filters

        self.assertEqual(path1, path2)
        self.assertEqual(parsed_qs1, parsed_qs2)