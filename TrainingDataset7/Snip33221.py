def test_tlds(self):
        """
        #16656 - Check urlize accepts more TLDs
        """
        self.assertEqual(
            urlize("usa.gov"), '<a href="https://usa.gov" rel="nofollow">usa.gov</a>'
        )