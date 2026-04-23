def test_create_new_instance_with_pk_equals_none_multi_inheritance(self):
        c1 = Congressman.objects.create(state="PA", name="John", title="senator 1")
        c2 = Person.objects.get(pk=c1.pk).congressman
        # Create a new congressman by setting pk = None.
        c2.pk = None
        c2.id = None
        c2.politician_ptr_id = None
        c2.name = "Bill"
        c2.title = "senator 2"
        c2.save()
        self.assertEqual(Congressman.objects.count(), 2)
        self.assertEqual(Person.objects.get(pk=c1.pk).name, "John")
        self.assertEqual(
            Politician.objects.get(pk=c1.politician_ptr_id).title,
            "senator 1",
        )