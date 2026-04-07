def test_regex_non_ascii(self):
        """
        A regex lookup does not trip on non-ASCII characters.
        """
        Player.objects.create(name="\u2660")
        Player.objects.get(name__regex="\u2660")