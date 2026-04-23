def test_error_dict_copy_attributes(self):
        class CustomRenderer(DjangoTemplates):
            pass

        renderer = CustomRenderer()
        e = ErrorDict(renderer=renderer)

        e_copy = copy.copy(e)
        self.assertEqual(e.renderer, e_copy.renderer)