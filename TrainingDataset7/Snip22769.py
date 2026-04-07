def test_form_with_iterable_boundfield(self):
        class BeatleForm(Form):
            name = ChoiceField(
                choices=[
                    ("john", "John"),
                    ("paul", "Paul"),
                    ("george", "George"),
                    ("ringo", "Ringo"),
                ],
                widget=RadioSelect,
            )

        f = BeatleForm(auto_id=False)
        self.assertHTMLEqual(
            "\n".join(str(bf) for bf in f["name"]),
            '<label><input type="radio" name="name" value="john" required> John</label>'
            '<label><input type="radio" name="name" value="paul" required> Paul</label>'
            '<label><input type="radio" name="name" value="george" required> George'
            "</label>"
            '<label><input type="radio" name="name" value="ringo" required> Ringo'
            "</label>",
        )
        self.assertHTMLEqual(
            "\n".join("<div>%s</div>" % bf for bf in f["name"]),
            """
            <div><label>
            <input type="radio" name="name" value="john" required> John</label></div>
            <div><label>
            <input type="radio" name="name" value="paul" required> Paul</label></div>
            <div><label>
            <input type="radio" name="name" value="george" required> George
            </label></div>
            <div><label>
            <input type="radio" name="name" value="ringo" required> Ringo</label></div>
            """,
        )