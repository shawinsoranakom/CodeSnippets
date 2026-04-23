def test_renderer_kwarg(self):
        custom = object()
        self.assertIs(ProductForm(renderer=custom).renderer, custom)