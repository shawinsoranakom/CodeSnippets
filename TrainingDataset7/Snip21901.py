def test_extended_length_storage(self):
        # Testing FileField with max_length > 255. Most systems have filename
        # length limitation of 255. Path takes extra chars.
        filename = (
            self._storage_max_filename_length(temp_storage) - 4
        ) * "a"  # 4 chars for extension.
        obj = Storage()
        obj.extended_length.save("%s.txt" % filename, ContentFile("Same Content"))
        self.assertEqual(obj.extended_length.name, "tests/%s.txt" % filename)
        self.assertEqual(obj.extended_length.read(), b"Same Content")
        obj.extended_length.close()