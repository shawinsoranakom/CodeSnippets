def test_proxy_included_in_ancestors(self):
        """
        Proxy models are included in the ancestors for a model's DoesNotExist,
        MultipleObjectsReturned, and NotUpdated
        """
        Person.objects.create(name="Foo McBar")
        MyPerson.objects.create(name="Bazza del Frob")
        LowerStatusPerson.objects.create(status="low", name="homer")
        max_id = Person.objects.aggregate(max_id=models.Max("id"))["max_id"]

        with self.assertRaises(Person.DoesNotExist):
            MyPersonProxy.objects.get(name="Zathras")
        with self.assertRaises(Person.MultipleObjectsReturned):
            MyPersonProxy.objects.get(id__lt=max_id + 1)
        with self.assertRaises(Person.DoesNotExist):
            StatusPerson.objects.get(name="Zathras")
        with self.assertRaises(Person.NotUpdated), transaction.atomic():
            StatusPerson(id=999).save(update_fields={"name"})

        StatusPerson.objects.create(name="Bazza Jr.")
        StatusPerson.objects.create(name="Foo Jr.")
        max_id = Person.objects.aggregate(max_id=models.Max("id"))["max_id"]

        with self.assertRaises(Person.MultipleObjectsReturned):
            StatusPerson.objects.get(id__lt=max_id + 1)