def test_error_list(self):
        e = ErrorList()
        e.append("Foo")
        e.append(ValidationError("Foo%(bar)s", code="foobar", params={"bar": "bar"}))

        self.assertIsInstance(e, list)
        self.assertIn("Foo", e)
        self.assertIn("Foo", ValidationError(e))

        self.assertEqual(e.as_text(), "* Foo\n* Foobar")

        self.assertEqual(
            e.as_ul(), '<ul class="errorlist"><li>Foo</li><li>Foobar</li></ul>'
        )

        errors = e.get_json_data()
        self.assertEqual(
            errors,
            [{"message": "Foo", "code": ""}, {"message": "Foobar", "code": "foobar"}],
        )
        self.assertEqual(json.dumps(errors), e.as_json())