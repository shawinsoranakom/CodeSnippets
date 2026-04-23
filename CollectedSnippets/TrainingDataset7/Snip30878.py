def test_wrong_type_lookup(self):
        """
        A ValueError is raised when the incorrect object type is passed to a
        query lookup.
        """
        # Passing incorrect object type
        with self.assertRaisesMessage(
            ValueError, self.error % (self.wrong_type, ObjectA._meta.object_name)
        ):
            ObjectB.objects.get(objecta=self.wrong_type)

        with self.assertRaisesMessage(
            ValueError, self.error % (self.wrong_type, ObjectA._meta.object_name)
        ):
            ObjectB.objects.filter(objecta__in=[self.wrong_type])

        with self.assertRaisesMessage(
            ValueError, self.error % (self.wrong_type, ObjectA._meta.object_name)
        ):
            ObjectB.objects.filter(objecta=self.wrong_type)

        with self.assertRaisesMessage(
            ValueError, self.error % (self.wrong_type, ObjectB._meta.object_name)
        ):
            ObjectA.objects.filter(objectb__in=[self.wrong_type, self.ob])

        # Passing an object of the class on which query is done.
        with self.assertRaisesMessage(
            ValueError, self.error % (self.ob, ObjectA._meta.object_name)
        ):
            ObjectB.objects.filter(objecta__in=[self.poa, self.ob])

        with self.assertRaisesMessage(
            ValueError, self.error % (self.ob, ChildObjectA._meta.object_name)
        ):
            ObjectC.objects.exclude(childobjecta__in=[self.coa, self.ob])