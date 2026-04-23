async def test_get_async_connection(self):
        with self.assertRaises(SynchronousOnlyOperation):
            list(SimpleModel.objects.all())