def test_eq(self):
        dirpath = "dir"
        file_name = "example"
        trans_file = TranslatableFile(
            dirpath=dirpath, file_name=file_name, locale_dir=None
        )
        trans_file_eq = TranslatableFile(
            dirpath=dirpath, file_name=file_name, locale_dir=None
        )
        trans_file_not_eq = TranslatableFile(
            dirpath="tmp", file_name=file_name, locale_dir=None
        )
        self.assertEqual(trans_file, trans_file_eq)
        self.assertNotEqual(trans_file, trans_file_not_eq)