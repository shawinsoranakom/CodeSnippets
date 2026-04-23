def test_content_type(self):
        ctype = ContentType.objects.get_for_model
        self.assertIs(ctype(Person), ctype(OtherPerson))