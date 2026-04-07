def test_dynamic_construction(self):
        # It's possible to construct a Form dynamically by adding to the
        # self.fields dictionary in __init__(). Don't forget to call
        # Form.__init__() within the subclass' __init__().
        class Person(Form):
            first_name = CharField()
            last_name = CharField()

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields["birthday"] = DateField()

        p = Person(auto_id=False)
        self.assertHTMLEqual(
            p.as_table(),
            """
            <tr><th>First name:</th><td>
            <input type="text" name="first_name" required></td></tr>
            <tr><th>Last name:</th><td>
            <input type="text" name="last_name" required></td></tr>
            <tr><th>Birthday:</th><td>
            <input type="text" name="birthday" required></td></tr>
            """,
        )

        # Instances of a dynamic Form do not persist fields from one Form
        # instance to the next.
        class MyForm(Form):
            def __init__(self, data=None, auto_id=False, field_list=[]):
                Form.__init__(self, data, auto_id=auto_id)

                for field in field_list:
                    self.fields[field[0]] = field[1]

        field_list = [("field1", CharField()), ("field2", CharField())]
        my_form = MyForm(field_list=field_list)
        self.assertHTMLEqual(
            my_form.as_table(),
            """
            <tr><th>Field1:</th><td><input type="text" name="field1" required></td></tr>
            <tr><th>Field2:</th><td><input type="text" name="field2" required></td></tr>
            """,
        )
        field_list = [("field3", CharField()), ("field4", CharField())]
        my_form = MyForm(field_list=field_list)
        self.assertHTMLEqual(
            my_form.as_table(),
            """
            <tr><th>Field3:</th><td><input type="text" name="field3" required></td></tr>
            <tr><th>Field4:</th><td><input type="text" name="field4" required></td></tr>
            """,
        )

        class MyForm(Form):
            default_field_1 = CharField()
            default_field_2 = CharField()

            def __init__(self, data=None, auto_id=False, field_list=[]):
                Form.__init__(self, data, auto_id=auto_id)

                for field in field_list:
                    self.fields[field[0]] = field[1]

        field_list = [("field1", CharField()), ("field2", CharField())]
        my_form = MyForm(field_list=field_list)
        self.assertHTMLEqual(
            my_form.as_table(),
            """
            <tr><th>Default field 1:</th><td>
            <input type="text" name="default_field_1" required></td></tr>
            <tr><th>Default field 2:</th><td>
            <input type="text" name="default_field_2" required></td></tr>
            <tr><th>Field1:</th><td><input type="text" name="field1" required></td></tr>
            <tr><th>Field2:</th><td><input type="text" name="field2" required></td></tr>
            """,
        )
        field_list = [("field3", CharField()), ("field4", CharField())]
        my_form = MyForm(field_list=field_list)
        self.assertHTMLEqual(
            my_form.as_table(),
            """
            <tr><th>Default field 1:</th><td>
            <input type="text" name="default_field_1" required></td></tr>
            <tr><th>Default field 2:</th><td>
            <input type="text" name="default_field_2" required></td></tr>
            <tr><th>Field3:</th><td><input type="text" name="field3" required></td></tr>
            <tr><th>Field4:</th><td><input type="text" name="field4" required></td></tr>
            """,
        )

        # Similarly, changes to field attributes do not persist from one Form
        # instance to the next.
        class Person(Form):
            first_name = CharField(required=False)
            last_name = CharField(required=False)

            def __init__(self, names_required=False, *args, **kwargs):
                super().__init__(*args, **kwargs)

                if names_required:
                    self.fields["first_name"].required = True
                    self.fields["first_name"].widget.attrs["class"] = "required"
                    self.fields["last_name"].required = True
                    self.fields["last_name"].widget.attrs["class"] = "required"

        f = Person(names_required=False)
        self.assertEqual(
            f["first_name"].field.required,
            f["last_name"].field.required,
            (False, False),
        )
        self.assertEqual(
            f["first_name"].field.widget.attrs,
            f["last_name"].field.widget.attrs,
            ({}, {}),
        )
        f = Person(names_required=True)
        self.assertEqual(
            f["first_name"].field.required, f["last_name"].field.required, (True, True)
        )
        self.assertEqual(
            f["first_name"].field.widget.attrs,
            f["last_name"].field.widget.attrs,
            ({"class": "reuired"}, {"class": "required"}),
        )
        f = Person(names_required=False)
        self.assertEqual(
            f["first_name"].field.required,
            f["last_name"].field.required,
            (False, False),
        )
        self.assertEqual(
            f["first_name"].field.widget.attrs,
            f["last_name"].field.widget.attrs,
            ({}, {}),
        )

        class Person(Form):
            first_name = CharField(max_length=30)
            last_name = CharField(max_length=30)

            def __init__(self, name_max_length=None, *args, **kwargs):
                super().__init__(*args, **kwargs)

                if name_max_length:
                    self.fields["first_name"].max_length = name_max_length
                    self.fields["last_name"].max_length = name_max_length

        f = Person(name_max_length=None)
        self.assertEqual(
            f["first_name"].field.max_length, f["last_name"].field.max_length, (30, 30)
        )
        f = Person(name_max_length=20)
        self.assertEqual(
            f["first_name"].field.max_length, f["last_name"].field.max_length, (20, 20)
        )
        f = Person(name_max_length=None)
        self.assertEqual(
            f["first_name"].field.max_length, f["last_name"].field.max_length, (30, 30)
        )

        # Similarly, choices do not persist from one Form instance to the next.
        # Refs #15127.
        class Person(Form):
            first_name = CharField(required=False)
            last_name = CharField(required=False)
            gender = ChoiceField(choices=(("f", "Female"), ("m", "Male")))

            def __init__(self, allow_unspec_gender=False, *args, **kwargs):
                super().__init__(*args, **kwargs)

                if allow_unspec_gender:
                    self.fields["gender"].choices += (("u", "Unspecified"),)

        f = Person()
        self.assertEqual(f["gender"].field.choices, [("f", "Female"), ("m", "Male")])
        f = Person(allow_unspec_gender=True)
        self.assertEqual(
            f["gender"].field.choices,
            [("f", "Female"), ("m", "Male"), ("u", "Unspecified")],
        )
        f = Person()
        self.assertEqual(f["gender"].field.choices, [("f", "Female"), ("m", "Male")])