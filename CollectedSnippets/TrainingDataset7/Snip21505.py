def test_negated_empty_exists(self):
        manager = Manager.objects.create()
        qs = Manager.objects.filter(~Exists(Manager.objects.none()) & Q(pk=manager.pk))
        self.assertSequenceEqual(qs, [manager])