def test_related_sliced_subquery(self):
        """
        Related objects constraints can safely contain sliced subqueries.
        refs #22434
        """
        generic = NamedCategory.objects.create(id=5, name="Generic")
        t1 = Tag.objects.create(name="t1", category=generic)
        t2 = Tag.objects.create(name="t2", category=generic)
        ManagedModel.objects.create(data="mm1", tag=t1, public=True)
        mm2 = ManagedModel.objects.create(data="mm2", tag=t2, public=True)

        query = ManagedModel.normal_manager.filter(
            tag__in=Tag.objects.order_by("-id")[:1]
        )
        self.assertEqual({x.id for x in query}, {mm2.id})