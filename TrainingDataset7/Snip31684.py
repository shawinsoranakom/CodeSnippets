def test_next_functionality(self):
        first_item = next(self.deserializer)

        self.assertEqual(first_item.object, self.jane)

        second_item = next(self.deserializer)
        self.assertEqual(second_item.object, self.joe)

        with self.assertRaises(StopIteration):
            next(self.deserializer)