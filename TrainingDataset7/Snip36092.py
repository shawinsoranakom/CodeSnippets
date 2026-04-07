def test_getitem_indexerror(self):
        choices = SimpleChoiceIterator()
        for i in (4, -4):
            with self.subTest(index=i):
                with self.assertRaises(IndexError) as ctx:
                    choices[i]
                self.assertTrue(str(ctx.exception).endswith("index out of range"))