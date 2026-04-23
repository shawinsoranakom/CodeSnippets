def test_delete_content_file(self):
        file = ContentFile(b"", name="foo")
        d = Document.objects.create(myfile=file)
        d.myfile.delete()
        self.assertIsNone(d.myfile.name)
        msg = "The 'myfile' attribute has no file associated with it."
        with self.assertRaisesMessage(ValueError, msg):
            getattr(d.myfile, "file")