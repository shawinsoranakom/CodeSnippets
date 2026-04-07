def test_not_supported(self):
        msg = "JSONObject() is not supported on this database backend."
        with self.assertRaisesMessage(NotSupportedError, msg):
            Author.objects.annotate(json_object=JSONObject()).get()