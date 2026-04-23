def test_long_non_ascii_text(self):
        """
        Inserting non-ASCII values with a length in the range 2001 to 4000
        characters, i.e. 4002 to 8000 bytes, must be set as a CLOB on Oracle
        (#22144).
        """
        Country.objects.bulk_create([Country(description="Ж" * 3000)])
        self.assertEqual(Country.objects.count(), 1)