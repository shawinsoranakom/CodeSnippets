def test_noniterable_arg_autoescape_off(self):
        obj = object()
        self.assertEqual(join(obj, "<br>", autoescape=False), obj)