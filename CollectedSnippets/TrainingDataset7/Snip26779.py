def test_call_time(self):
        self.assertEqual(pre_migrate_receiver.call_counter, 1)
        self.assertEqual(post_migrate_receiver.call_counter, 1)