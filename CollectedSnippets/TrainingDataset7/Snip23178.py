def test_unicode_filename(self):
        # FileModel with Unicode filename and data.
        file1 = SimpleUploadedFile(
            "我隻氣墊船裝滿晒鱔.txt",
            "मेरी मँडराने वाली नाव सर्पमीनों से भरी ह".encode(),
        )
        f = FileForm(data={}, files={"file1": file1}, auto_id=False)
        self.assertTrue(f.is_valid())
        self.assertIn("file1", f.cleaned_data)
        m = FileModel.objects.create(file=f.cleaned_data["file1"])
        self.assertEqual(
            m.file.name,
            "tests/\u6211\u96bb\u6c23\u588a\u8239\u88dd\u6eff\u6652\u9c54.txt",
        )
        m.file.delete()
        m.delete()