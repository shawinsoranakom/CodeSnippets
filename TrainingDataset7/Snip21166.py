def test_delete_proxy_pair(self):
        """
        If a pair of proxy models are linked by an FK from one concrete parent
        to the other, deleting one proxy model cascade-deletes the other, and
        the deletion happens in the right order (not triggering an
        IntegrityError on databases unable to defer integrity checks).

        Refs #17918.
        """
        # Create an Image (proxy of File) and FooFileProxy (proxy of FooFile,
        # which has an FK to File)
        image = Image.objects.create()
        as_file = File.objects.get(pk=image.pk)
        FooFileProxy.objects.create(my_file=as_file)

        Image.objects.all().delete()

        self.assertEqual(len(FooFileProxy.objects.all()), 0)