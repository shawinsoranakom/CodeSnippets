def test_get_content_type_no_arguments(self):
        field = Answer._meta.get_field("question")
        with self.assertRaisesMessage(
            Exception, "Impossible arguments to GFK.get_content_type!"
        ):
            field.get_content_type()