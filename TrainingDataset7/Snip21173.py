def test_meta_ordered_delete(self):
        # When a subquery is performed by deletion code, the subquery must be
        # cleared of all ordering. There was a but that caused _meta ordering
        # to be used. Refs #19720.
        h = House.objects.create(address="Foo")
        OrderedPerson.objects.create(name="Jack", lives_in=h)
        OrderedPerson.objects.create(name="Bob", lives_in=h)
        OrderedPerson.objects.filter(lives_in__address="Foo").delete()
        self.assertEqual(OrderedPerson.objects.count(), 0)