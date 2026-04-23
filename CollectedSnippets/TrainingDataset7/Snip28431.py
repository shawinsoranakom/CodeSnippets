def test_file_field_multiple_save(self):
        """
        Simulate a file upload and check how many times Model.save() gets
        called. Test for bug #639.
        """

        class PhotoForm(forms.ModelForm):
            class Meta:
                model = Photo
                fields = "__all__"

        # Grab an image for testing.
        filename = os.path.join(os.path.dirname(__file__), "test.png")
        with open(filename, "rb") as fp:
            img = fp.read()

        # Fake a POST QueryDict and FILES MultiValueDict.
        data = {"title": "Testing"}
        files = {"image": SimpleUploadedFile("test.png", img, "image/png")}

        form = PhotoForm(data=data, files=files)
        p = form.save()

        try:
            # Check the savecount stored on the object (see the model).
            self.assertEqual(p._savecount, 1)
        finally:
            # Delete the "uploaded" file to avoid clogging /tmp.
            p = Photo.objects.get()
            p.image.delete(save=False)