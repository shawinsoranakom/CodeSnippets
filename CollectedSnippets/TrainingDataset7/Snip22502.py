def test_choicefield_grouped_mapping(self):
        f = ChoiceField(
            choices={
                "Numbers": (("1", "One"), ("2", "Two")),
                "Letters": (("3", "A"), ("4", "B")),
            }
        )
        for i in ("1", "2", "3", "4"):
            with self.subTest(i):
                self.assertEqual(i, f.clean(i))