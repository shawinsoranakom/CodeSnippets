def test_latest_manual(self):
        # You can still use latest() with a model that doesn't have
        # "get_latest_by" set -- just pass in the field name manually.
        Person.objects.create(name="Ralph", birthday=datetime(1950, 1, 1))
        p2 = Person.objects.create(name="Stephanie", birthday=datetime(1960, 2, 3))
        msg = (
            "earliest() and latest() require either fields as positional arguments "
            "or 'get_latest_by' in the model's Meta."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Person.objects.latest()
        self.assertEqual(Person.objects.latest("birthday"), p2)