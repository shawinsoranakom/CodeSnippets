def test_queryset_delete_returns_num_rows(self):
        """
        QuerySet.delete() should return the number of deleted rows and a
        dictionary with the number of deletions for each object type.
        """
        Avatar.objects.bulk_create(
            [Avatar(desc="a"), Avatar(desc="b"), Avatar(desc="c")]
        )
        avatars_count = Avatar.objects.count()
        deleted, rows_count = Avatar.objects.all().delete()
        self.assertEqual(deleted, avatars_count)

        # more complex example with multiple object types
        r = R.objects.create()
        h1 = HiddenUser.objects.create(r=r)
        HiddenUser.objects.create(r=r)
        HiddenUserProfile.objects.create(user=h1)
        existed_objs = {
            R._meta.label: R.objects.count(),
            HiddenUser._meta.label: HiddenUser.objects.count(),
            HiddenUserProfile._meta.label: HiddenUserProfile.objects.count(),
        }
        deleted, deleted_objs = R.objects.all().delete()
        self.assertCountEqual(deleted_objs.keys(), existed_objs.keys())
        for k, v in existed_objs.items():
            self.assertEqual(deleted_objs[k], v)