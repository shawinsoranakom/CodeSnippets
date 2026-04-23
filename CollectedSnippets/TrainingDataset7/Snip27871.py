def test_save_content_file_without_name(self):
        d = Document()
        d.myfile = ContentFile(b"")
        msg = "File for myfile must have the name attribute specified to be saved."
        with self.assertRaisesMessage(FieldError, msg) as cm:
            d.save()

        self.assertEqual(
            cm.exception.__notes__, ["Pass a 'name' argument to ContentFile."]
        )