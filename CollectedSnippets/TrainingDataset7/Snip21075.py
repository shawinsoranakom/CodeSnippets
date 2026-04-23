def test_save(self):
        with self.assertRaisesMessage(AttributeError, self.expected_msg):
            self.deferred_item.save(force_insert=True)
        with self.assertRaisesMessage(AttributeError, self.expected_msg):
            self.deferred_item.save()