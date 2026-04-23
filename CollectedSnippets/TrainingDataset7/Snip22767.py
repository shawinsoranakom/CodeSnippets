def test_forms_with_choices(self):
        # For a form with a <select>, use ChoiceField:
        class FrameworkForm(Form):
            name = CharField()
            language = ChoiceField(choices=[("P", "Python"), ("J", "Java")])

        f = FrameworkForm(auto_id=False)
        self.assertHTMLEqual(
            str(f["language"]),
            """<select name="language">
<option value="P">Python</option>
<option value="J">Java</option>
</select>""",
        )
        f = FrameworkForm({"name": "Django", "language": "P"}, auto_id=False)
        self.assertHTMLEqual(
            str(f["language"]),
            """<select name="language">
<option value="P" selected>Python</option>
<option value="J">Java</option>
</select>""",
        )

        # A subtlety: If one of the choices' value is the empty string and the
        # form is unbound, then the <option> for the empty-string choice will
        # get selected.
        class FrameworkForm(Form):
            name = CharField()
            language = ChoiceField(
                choices=[("", "------"), ("P", "Python"), ("J", "Java")]
            )

        f = FrameworkForm(auto_id=False)
        self.assertHTMLEqual(
            str(f["language"]),
            """<select name="language" required>
<option value="" selected>------</option>
<option value="P">Python</option>
<option value="J">Java</option>
</select>""",
        )

        # You can specify widget attributes in the Widget constructor.
        class FrameworkForm(Form):
            name = CharField()
            language = ChoiceField(
                choices=[("P", "Python"), ("J", "Java")],
                widget=Select(attrs={"class": "foo"}),
            )

        f = FrameworkForm(auto_id=False)
        self.assertHTMLEqual(
            str(f["language"]),
            """<select class="foo" name="language">
<option value="P">Python</option>
<option value="J">Java</option>
</select>""",
        )
        f = FrameworkForm({"name": "Django", "language": "P"}, auto_id=False)
        self.assertHTMLEqual(
            str(f["language"]),
            """<select class="foo" name="language">
<option value="P" selected>Python</option>
<option value="J">Java</option>
</select>""",
        )

        # When passing a custom widget instance to ChoiceField, note that
        # setting 'choices' on the widget is meaningless. The widget will use
        # the choices defined on the Field, not the ones defined on the Widget.
        class FrameworkForm(Form):
            name = CharField()
            language = ChoiceField(
                choices=[("P", "Python"), ("J", "Java")],
                widget=Select(
                    choices=[("R", "Ruby"), ("P", "Perl")], attrs={"class": "foo"}
                ),
            )

        f = FrameworkForm(auto_id=False)
        self.assertHTMLEqual(
            str(f["language"]),
            """<select class="foo" name="language">
<option value="P">Python</option>
<option value="J">Java</option>
</select>""",
        )
        f = FrameworkForm({"name": "Django", "language": "P"}, auto_id=False)
        self.assertHTMLEqual(
            str(f["language"]),
            """<select class="foo" name="language">
<option value="P" selected>Python</option>
<option value="J">Java</option>
</select>""",
        )

        # You can set a ChoiceField's choices after the fact.
        class FrameworkForm(Form):
            name = CharField()
            language = ChoiceField()

        f = FrameworkForm(auto_id=False)
        self.assertHTMLEqual(
            str(f["language"]),
            """<select name="language">
</select>""",
        )
        f.fields["language"].choices = [("P", "Python"), ("J", "Java")]
        self.assertHTMLEqual(
            str(f["language"]),
            """<select name="language">
<option value="P">Python</option>
<option value="J">Java</option>
</select>""",
        )