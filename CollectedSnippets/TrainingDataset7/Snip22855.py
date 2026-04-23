def test_error_list_class_not_specified(self):
        e = ErrorList()
        e.append("Foo")
        e.append(ValidationError("Foo%(bar)s", code="foobar", params={"bar": "bar"}))
        self.assertEqual(
            e.as_ul(), '<ul class="errorlist"><li>Foo</li><li>Foobar</li></ul>'
        )