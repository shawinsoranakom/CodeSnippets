def test_delete_concrete_parent(self):
        """
        Deleting an instance of a concrete model should also delete objects
        referencing its proxy subclass.
        """
        self.create_image()

        File.objects.all().delete()

        # A File deletion == Image deletion
        self.assertEqual(len(File.objects.all()), 0)
        self.assertEqual(len(Image.objects.all()), 0)

        # The File deletion should have cascaded and deleted *all* references
        # to it.
        self.assertEqual(len(FooFile.objects.all()), 0)
        self.assertEqual(len(FooImage.objects.all()), 0)