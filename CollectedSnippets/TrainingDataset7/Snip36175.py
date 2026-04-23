def test_dict_translation(self):
        mvd = MultiValueDict(
            {
                "devs": ["Bob", "Joe"],
                "pm": ["Rory"],
            }
        )
        d = mvd.dict()
        self.assertEqual(list(d), list(mvd))
        for key in mvd:
            self.assertEqual(d[key], mvd[key])

        self.assertEqual({}, MultiValueDict().dict())