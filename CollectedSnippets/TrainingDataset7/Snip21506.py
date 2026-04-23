def test_select_negated_empty_exists(self):
        manager = Manager.objects.create()
        qs = Manager.objects.annotate(
            not_exists=~Exists(Manager.objects.none())
        ).filter(pk=manager.pk)
        self.assertSequenceEqual(qs, [manager])
        self.assertIs(qs.get().not_exists, True)