def test_subquery_filter_by_lazy(self):
        self.max.manager = Manager.objects.create(name="Manager")
        self.max.save()
        max_manager = SimpleLazyObject(
            lambda: Manager.objects.get(pk=self.max.manager.pk)
        )
        qs = Company.objects.annotate(
            ceo_manager=Subquery(
                Employee.objects.filter(
                    lastname=OuterRef("ceo__lastname"),
                ).values("manager"),
            ),
        ).filter(ceo_manager=max_manager)
        self.assertEqual(qs.get(), self.gmbh)