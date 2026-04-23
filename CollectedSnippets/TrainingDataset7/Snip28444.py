def test_callable_field_default(self):
        class PublicationDefaultsForm(forms.ModelForm):
            class Meta:
                model = PublicationDefaults
                fields = ("title", "date_published", "mode", "category")

        self.maxDiff = 2000
        form = PublicationDefaultsForm()
        today_str = str(datetime.date.today())
        self.assertHTMLEqual(
            form.as_p(),
            """
            <p><label for="id_title">Title:</label>
            <input id="id_title" maxlength="30" name="title" type="text" required>
            </p>
            <p><label for="id_date_published">Date published:</label>
            <input id="id_date_published" name="date_published" type="text" value="{0}"
                required>
            <input id="initial-id_date_published" name="initial-date_published"
                type="hidden" value="{0}">
            </p>
            <p><label for="id_mode">Mode:</label> <select id="id_mode" name="mode">
            <option value="di" selected>direct</option>
            <option value="de">delayed</option></select>
            <input id="initial-id_mode" name="initial-mode" type="hidden" value="di">
            </p>
            <p>
            <label for="id_category">Category:</label>
            <select id="id_category" name="category">
            <option value="1">Games</option>
            <option value="2">Comics</option>
            <option value="3" selected>Novel</option></select>
            <input id="initial-id_category" name="initial-category" type="hidden"
                value="3">
            """.format(today_str),
        )
        empty_data = {
            "title": "",
            "date_published": today_str,
            "initial-date_published": today_str,
            "mode": "di",
            "initial-mode": "di",
            "category": "3",
            "initial-category": "3",
        }
        bound_form = PublicationDefaultsForm(empty_data)
        self.assertFalse(bound_form.has_changed())