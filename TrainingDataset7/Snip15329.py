def test_publish_parts(self):
        """
        Django shouldn't break the default role for interpreted text
        when ``publish_parts`` is used directly, by setting it to
        ``cmsreference`` (#6681).
        """
        import docutils

        self.assertNotEqual(
            docutils.parsers.rst.roles.DEFAULT_INTERPRETED_ROLE, "cmsreference"
        )
        source = "reST, `interpreted text`, default role."
        markup = "<p>reST, <cite>interpreted text</cite>, default role.</p>\n"
        parts = docutils.core.publish_parts(source=source, writer="html4css1")
        self.assertEqual(parts["fragment"], markup)