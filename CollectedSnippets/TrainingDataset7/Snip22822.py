def test_subclassing_forms(self):
        # You can subclass a Form to add fields. The resulting form subclass
        # will have all of the fields of the parent Form, plus whichever fields
        # you define in the subclass.
        class Person(Form):
            first_name = CharField()
            last_name = CharField()
            birthday = DateField()

        class Musician(Person):
            instrument = CharField()

        p = Person(auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """<li>First name: <input type="text" name="first_name" required></li>
<li>Last name: <input type="text" name="last_name" required></li>
<li>Birthday: <input type="text" name="birthday" required></li>""",
        )
        m = Musician(auto_id=False)
        self.assertHTMLEqual(
            m.as_ul(),
            """<li>First name: <input type="text" name="first_name" required></li>
<li>Last name: <input type="text" name="last_name" required></li>
<li>Birthday: <input type="text" name="birthday" required></li>
<li>Instrument: <input type="text" name="instrument" required></li>""",
        )

        # Yes, you can subclass multiple forms. The fields are added in the
        # order in which the parent classes are listed.
        class Person(Form):
            first_name = CharField()
            last_name = CharField()
            birthday = DateField()

        class Instrument(Form):
            instrument = CharField()

        class Beatle(Person, Instrument):
            haircut_type = CharField()

        b = Beatle(auto_id=False)
        self.assertHTMLEqual(
            b.as_ul(),
            """<li>Instrument: <input type="text" name="instrument" required></li>
<li>First name: <input type="text" name="first_name" required></li>
<li>Last name: <input type="text" name="last_name" required></li>
<li>Birthday: <input type="text" name="birthday" required></li>
<li>Haircut type: <input type="text" name="haircut_type" required></li>""",
        )