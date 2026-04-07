def test_keep_parents_does_not_delete_proxy_related(self):
        r_child = RChild.objects.create()
        r_proxy = RProxy.objects.get(pk=r_child.pk)
        Origin.objects.create(r_proxy=r_proxy)
        self.assertEqual(Origin.objects.count(), 1)
        r_child.delete(keep_parents=True)
        self.assertEqual(Origin.objects.count(), 1)