def test_values_queryset_lookup(self):
        """
        ValueQuerySets are not checked for compatibility with the lookup field.
        """
        # Make sure the num and objecta field values match.
        ob = ObjectB.objects.get(name="ob")
        ob.num = ob.objecta.pk
        ob.save()
        pob = ObjectB.objects.get(name="pob")
        pob.num = pob.objecta.pk
        pob.save()
        self.assertSequenceEqual(
            ObjectB.objects.filter(
                objecta__in=ObjectB.objects.values_list("num")
            ).order_by("pk"),
            [ob, pob],
        )