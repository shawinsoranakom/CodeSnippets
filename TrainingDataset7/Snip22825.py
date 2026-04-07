def test_forms_with_null_boolean(self):
        # NullBooleanField is a bit of a special case because its presentation
        # (widget) is different than its data. This is handled transparently,
        # though.
        class Person(Form):
            name = CharField()
            is_cool = NullBooleanField()

        p = Person({"name": "Joe"}, auto_id=False)
        self.assertHTMLEqual(
            str(p["is_cool"]),
            """<select name="is_cool">
<option value="unknown" selected>Unknown</option>
<option value="true">Yes</option>
<option value="false">No</option>
</select>""",
        )
        p = Person({"name": "Joe", "is_cool": "1"}, auto_id=False)
        self.assertHTMLEqual(
            str(p["is_cool"]),
            """<select name="is_cool">
<option value="unknown" selected>Unknown</option>
<option value="true">Yes</option>
<option value="false">No</option>
</select>""",
        )
        p = Person({"name": "Joe", "is_cool": "2"}, auto_id=False)
        self.assertHTMLEqual(
            str(p["is_cool"]),
            """<select name="is_cool">
<option value="unknown">Unknown</option>
<option value="true" selected>Yes</option>
<option value="false">No</option>
</select>""",
        )
        p = Person({"name": "Joe", "is_cool": "3"}, auto_id=False)
        self.assertHTMLEqual(
            str(p["is_cool"]),
            """<select name="is_cool">
<option value="unknown">Unknown</option>
<option value="true">Yes</option>
<option value="false" selected>No</option>
</select>""",
        )
        p = Person({"name": "Joe", "is_cool": True}, auto_id=False)
        self.assertHTMLEqual(
            str(p["is_cool"]),
            """<select name="is_cool">
<option value="unknown">Unknown</option>
<option value="true" selected>Yes</option>
<option value="false">No</option>
</select>""",
        )
        p = Person({"name": "Joe", "is_cool": False}, auto_id=False)
        self.assertHTMLEqual(
            str(p["is_cool"]),
            """<select name="is_cool">
<option value="unknown">Unknown</option>
<option value="true">Yes</option>
<option value="false" selected>No</option>
</select>""",
        )
        p = Person({"name": "Joe", "is_cool": "unknown"}, auto_id=False)
        self.assertHTMLEqual(
            str(p["is_cool"]),
            """<select name="is_cool">
<option value="unknown" selected>Unknown</option>
<option value="true">Yes</option>
<option value="false">No</option>
</select>""",
        )
        p = Person({"name": "Joe", "is_cool": "true"}, auto_id=False)
        self.assertHTMLEqual(
            str(p["is_cool"]),
            """<select name="is_cool">
<option value="unknown">Unknown</option>
<option value="true" selected>Yes</option>
<option value="false">No</option>
</select>""",
        )
        p = Person({"name": "Joe", "is_cool": "false"}, auto_id=False)
        self.assertHTMLEqual(
            str(p["is_cool"]),
            """<select name="is_cool">
<option value="unknown">Unknown</option>
<option value="true">Yes</option>
<option value="false" selected>No</option>
</select>""",
        )