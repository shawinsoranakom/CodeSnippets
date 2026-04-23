def test_wrong_backward_lookup(self):
        """
        A ValueError is raised when the incorrect object type is passed to a
        query lookup for backward relations.
        """
        with self.assertRaisesMessage(
            ValueError, self.error % (self.oa, ObjectB._meta.object_name)
        ):
            ObjectA.objects.filter(objectb__in=[self.oa, self.ob])

        with self.assertRaisesMessage(
            ValueError, self.error % (self.oa, ObjectB._meta.object_name)
        ):
            ObjectA.objects.exclude(objectb=self.oa)

        with self.assertRaisesMessage(
            ValueError, self.error % (self.wrong_type, ObjectB._meta.object_name)
        ):
            ObjectA.objects.get(objectb=self.wrong_type)