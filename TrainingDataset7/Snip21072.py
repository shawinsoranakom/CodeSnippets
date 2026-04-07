def test_delete_defered_model(self):
        Item.objects.only("value").get(pk=self.item_pk).delete()
        self.assertEqual(self.pre_delete_senders, [Item])
        self.assertEqual(self.post_delete_senders, [Item])