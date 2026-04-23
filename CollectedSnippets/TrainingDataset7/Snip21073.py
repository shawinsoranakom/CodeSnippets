def test_delete_defered_proxy_model(self):
        Proxy.objects.only("value").get(pk=self.item_pk).delete()
        self.assertEqual(self.pre_delete_senders, [Proxy])
        self.assertEqual(self.post_delete_senders, [Proxy])