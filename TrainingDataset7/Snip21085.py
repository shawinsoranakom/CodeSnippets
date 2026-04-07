def test_db_setnull(self):
        a = SetNullDbModel.objects.create(
            db_setnull=RelatedDbOptionParent.objects.create()
        )
        a.db_setnull.delete()
        a = SetNullDbModel.objects.get(pk=a.pk)
        self.assertIsNone(a.db_setnull)