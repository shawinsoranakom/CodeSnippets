def test_multivaluedict(self):
        result = urlencode(
            MultiValueDict(
                {
                    "name": ["Adrian", "Simon"],
                    "position": ["Developer"],
                }
            ),
            doseq=True,
        )
        self.assertEqual(result, "name=Adrian&name=Simon&position=Developer")