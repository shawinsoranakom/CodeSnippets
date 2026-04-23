def test_relation_unsaved(self):
        Third.objects.create(name="Third 1")
        Third.objects.create(name="Third 2")
        th = Third(name="testing")
        # The object isn't saved and the relation cannot be used.
        msg = (
            "'Third' instance needs to have a primary key value before this "
            "relationship can be used."
        )
        with self.assertRaisesMessage(ValueError, msg):
            th.child_set.count()
        # The reverse foreign key manager can be created.
        self.assertEqual(th.child_set.model, Third)

        th.save()
        # Now the model is saved, so we will need to execute a query.
        with self.assertNumQueries(1):
            self.assertEqual(th.child_set.count(), 0)