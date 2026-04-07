def test_custom_ignore_patterns(self):
        """
        A custom ignore_patterns list, ['*.css', '*/vendor/*.js'] in this case,
        can be specified in an AppConfig definition.
        """
        self.assertFileNotFound("test/nonascii.css")
        self.assertFileContains("test/.hidden", "should be ignored")
        self.assertFileNotFound(os.path.join("test", "vendor", "module.js"))