def test_filter_by_empty_exists(self):
        manager = Manager.objects.create()
        qs = Manager.objects.annotate(exists=Exists(Manager.objects.none())).filter(
            pk=manager.pk, exists=False
        )
        self.assertSequenceEqual(qs, [manager])
        self.assertIs(qs.get().exists, False)