def test_error_list_class_has_one_class_specified(self):
        e = ErrorList(error_class="foobar-error-class")
        e.append("Foo")
        e.append(ValidationError("Foo%(bar)s", code="foobar", params={"bar": "bar"}))
        self.assertEqual(
            e.as_ul(),
            '<ul class="errorlist foobar-error-class"><li>Foo</li><li>Foobar</li></ul>',
        )