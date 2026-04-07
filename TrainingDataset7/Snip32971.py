def test_noniterable_arg(self):
        obj = object()
        self.assertEqual(join(obj, "<br>"), obj)