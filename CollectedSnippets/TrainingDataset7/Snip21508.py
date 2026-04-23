def test_annotate_by_empty_custom_exists(self):
        class CustomExists(Exists):
            template = Subquery.template

        manager = Manager.objects.create()
        qs = Manager.objects.annotate(exists=CustomExists(Manager.objects.none()))
        self.assertSequenceEqual(qs, [manager])
        self.assertIs(qs.get().exists, False)