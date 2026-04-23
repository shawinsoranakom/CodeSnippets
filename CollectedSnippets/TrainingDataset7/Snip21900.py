def test_file_truncation(self):
        # Given the max_length is limited, when multiple files get uploaded
        # under the same name, then the filename get truncated in order to fit
        # in _(7 random chars). When most of the max_length is taken by
        # dirname + extension and there are not enough  characters in the
        # filename to truncate, an exception should be raised.
        objs = [Storage() for i in range(2)]
        filename = "filename.ext"

        for o in objs:
            o.limited_length.save(filename, ContentFile("Same Content"))
        try:
            # Testing truncation.
            names = [o.limited_length.name for o in objs]
            self.assertEqual(names[0], "tests/%s" % filename)
            self.assertRegex(names[1], "tests/fi_%s.ext" % FILE_SUFFIX_REGEX)

            # Testing exception is raised when filename is too short to
            # truncate.
            filename = "short.longext"
            objs[0].limited_length.save(filename, ContentFile("Same Content"))
            with self.assertRaisesMessage(
                SuspiciousFileOperation, "Storage can not find an available filename"
            ):
                objs[1].limited_length.save(*(filename, ContentFile("Same Content")))
        finally:
            for o in objs:
                o.delete()