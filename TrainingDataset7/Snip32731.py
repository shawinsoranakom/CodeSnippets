def test_call_task(self):
        self.assertEqual(test_tasks.calculate_meaning_of_life.call(), 42)