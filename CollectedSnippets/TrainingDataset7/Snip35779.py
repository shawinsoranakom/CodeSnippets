def test_view_func_from_cbv(self):
        expected = "/hello/world/"
        url = reverse(views.view_func_from_cbv, kwargs={"name": "world"})
        self.assertEqual(url, expected)