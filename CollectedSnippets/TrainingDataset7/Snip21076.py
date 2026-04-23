def test_bulk_create(self):
        with self.assertRaisesMessage(AttributeError, self.expected_msg):
            SimpleItem.objects.bulk_create([self.deferred_item])