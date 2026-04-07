def test_ignore_conflicts_ignore(self):
        data = [
            TwoFields(f1=1, f2=1),
            TwoFields(f1=2, f2=2),
            TwoFields(f1=3, f2=3),
        ]
        TwoFields.objects.bulk_create(data)
        self.assertEqual(TwoFields.objects.count(), 3)
        # With ignore_conflicts=True, conflicts are ignored.
        conflicting_objects = [
            TwoFields(f1=2, f2=2),
            TwoFields(f1=3, f2=3),
        ]
        TwoFields.objects.bulk_create([conflicting_objects[0]], ignore_conflicts=True)
        TwoFields.objects.bulk_create(conflicting_objects, ignore_conflicts=True)
        self.assertEqual(TwoFields.objects.count(), 3)
        self.assertIsNone(conflicting_objects[0].pk)
        self.assertIsNone(conflicting_objects[1].pk)
        # New objects are created and conflicts are ignored.
        new_object = TwoFields(f1=4, f2=4)
        TwoFields.objects.bulk_create(
            conflicting_objects + [new_object], ignore_conflicts=True
        )
        self.assertEqual(TwoFields.objects.count(), 4)
        self.assertIsNone(new_object.pk)
        # Without ignore_conflicts=True, there's a problem.
        with self.assertRaises(IntegrityError):
            TwoFields.objects.bulk_create(conflicting_objects)