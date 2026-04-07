def test_num_args(self):
        with self.assertRaisesMessage(
            TypeError, "'Lower' takes exactly 1 argument (2 given)"
        ):
            Author.objects.update(name=Lower("name", "name"))