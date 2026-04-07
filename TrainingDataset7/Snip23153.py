def test_error_list_copy_attributes(self):
        class CustomRenderer(DjangoTemplates):
            pass

        renderer = CustomRenderer()
        e = ErrorList(error_class="woopsies", renderer=renderer)

        e_copy = e.copy()
        self.assertEqual(e.error_class, e_copy.error_class)
        self.assertEqual(e.renderer, e_copy.renderer)