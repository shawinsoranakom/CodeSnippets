def test_pickle(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with override_settings(MEDIA_ROOT=Path(tmp_dir)):
                with open(__file__, "rb") as fp:
                    file1 = File(fp, name="test_file.py")
                    document = Document(myfile="test_file.py")
                    document.myfile.save("test_file.py", file1)
                    try:
                        dump = pickle.dumps(document)
                        loaded_document = pickle.loads(dump)
                        self.assertEqual(document.myfile, loaded_document.myfile)
                        self.assertEqual(
                            document.myfile.url,
                            loaded_document.myfile.url,
                        )
                        self.assertEqual(
                            document.myfile.storage,
                            loaded_document.myfile.storage,
                        )
                        self.assertEqual(
                            document.myfile.instance,
                            loaded_document.myfile.instance,
                        )
                        self.assertEqual(
                            document.myfile.field,
                            loaded_document.myfile.field,
                        )
                        myfile_dump = pickle.dumps(document.myfile)
                        loaded_myfile = pickle.loads(myfile_dump)
                        self.assertEqual(document.myfile, loaded_myfile)
                        self.assertEqual(document.myfile.url, loaded_myfile.url)
                        self.assertEqual(
                            document.myfile.storage,
                            loaded_myfile.storage,
                        )
                        self.assertEqual(
                            document.myfile.instance,
                            loaded_myfile.instance,
                        )
                        self.assertEqual(document.myfile.field, loaded_myfile.field)
                    finally:
                        document.myfile.delete()