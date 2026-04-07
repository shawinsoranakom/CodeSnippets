def test_fallback_language_code(self):
        """
        get_language_info return the first fallback language info if the
        lang_info struct does not contain the 'name' key.
        """
        li = get_language_info("zh-my")
        self.assertEqual(li["code"], "zh-hans")
        li = get_language_info("zh-hans")
        self.assertEqual(li["code"], "zh-hans")