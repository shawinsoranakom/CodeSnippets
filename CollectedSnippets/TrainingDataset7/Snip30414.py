def test_bulk_insert(self):
        objs = [ReturningModel(), ReturningModel(pk=2**11), ReturningModel()]
        ReturningModel.objects.bulk_create(objs)
        for obj in objs:
            with self.subTest(obj=obj):
                self.assertTrue(obj.pk)
                self.assertIsInstance(obj.created, datetime.datetime)