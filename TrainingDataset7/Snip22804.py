def test_boundfield_initial_called_once(self):
        """
        Multiple calls to BoundField().value() in an unbound form should return
        the same result each time (#24391).
        """

        class MyForm(Form):
            name = CharField(max_length=10, initial=uuid.uuid4)

        form = MyForm()
        name = form["name"]
        self.assertEqual(name.value(), name.value())
        # BoundField is also cached
        self.assertIs(form["name"], name)