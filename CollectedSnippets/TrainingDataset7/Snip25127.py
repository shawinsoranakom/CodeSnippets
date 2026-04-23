def test_sparse_territory_catalog(self):
        """
        Untranslated strings for territorial language variants use the
        translations of the generic language. In this case, the de-de
        translation falls back to de.
        """
        with translation.override("de-de"):
            self.assertGettext("Test 1 (en)", "(de-de)")
            self.assertGettext("Test 2 (en)", "(de)")