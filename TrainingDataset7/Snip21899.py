def test_duplicate_filename(self):
        # Multiple files with the same name get _(7 random chars) appended to
        # them.
        tests = [
            ("multiple_files", "txt"),
            ("multiple_files_many_extensions", "tar.gz"),
        ]
        for filename, extension in tests:
            with self.subTest(filename=filename):
                objs = [Storage() for i in range(2)]
                for o in objs:
                    o.normal.save(f"{filename}.{extension}", ContentFile("Content"))
                try:
                    names = [o.normal.name for o in objs]
                    self.assertEqual(names[0], f"tests/{filename}.{extension}")
                    self.assertRegex(
                        names[1], f"tests/{filename}_{FILE_SUFFIX_REGEX}.{extension}"
                    )
                finally:
                    for o in objs:
                        o.delete()