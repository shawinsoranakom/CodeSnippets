def test_not_supported(self):
        msg = "JSONFields are not supported on this database backend."
        with self.assertRaisesMessage(NotSupportedError, msg):
            Author.objects.annotate(json_array=JSONArray()).first()