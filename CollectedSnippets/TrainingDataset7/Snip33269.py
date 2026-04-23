def test_false_arguments(self):
        self.assertEqual(
            yesno(False, "certainly,get out of town,perhaps"), "get out of town"
        )