def test_unknown_format(self):
        msg = "DOES NOT EXIST is not a recognized format."
        if connection.features.supported_explain_formats:
            msg += " Allowed formats: %s" % ", ".join(
                sorted(connection.features.supported_explain_formats)
            )
        else:
            msg += f" {connection.display_name} does not support any formats."
        with self.assertRaisesMessage(ValueError, msg):
            Tag.objects.explain(format="does not exist")