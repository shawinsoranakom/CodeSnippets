def test_control_char_failure(self):
        """
        Serializing control characters with XML should fail as those characters
        are not supported in the XML 1.0 standard (except HT, LF, CR).
        """
        self.a1.headline = "This contains \u0001 control \u0011 chars"
        msg = "Article.headline (pk:%s) contains unserializable characters" % self.a1.pk
        with self.assertRaisesMessage(ValueError, msg):
            serializers.serialize(self.serializer_name, [self.a1])
        self.a1.headline = "HT \u0009, LF \u000a, and CR \u000d are allowed"
        self.assertIn(
            "HT \t, LF \n, and CR \r are allowed",
            serializers.serialize(self.serializer_name, [self.a1]),
        )