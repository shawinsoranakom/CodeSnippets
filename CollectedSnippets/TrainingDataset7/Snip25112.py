def test_special_fallback_language(self):
        """
        Some languages may have special fallbacks that don't follow the simple
        'fr-ca' -> 'fr' logic (notably Chinese codes).
        """
        request = self.rf.get("/", headers={"accept-language": "zh-my,en"})
        self.assertEqual(get_language_from_request(request), "zh-hans")