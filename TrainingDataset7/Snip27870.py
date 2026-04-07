def test_save_without_name(self):
        with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
            document = Document.objects.create(myfile="something.txt")
            document.myfile = File(tmp)
            msg = f"Detected path traversal attempt in '{tmp.name}'"
            with self.assertRaisesMessage(SuspiciousFileOperation, msg):
                document.save()