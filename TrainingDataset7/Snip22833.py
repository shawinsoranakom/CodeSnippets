def test_error_html_required_html_classes(self):
        class Person(Form):
            name = CharField()
            is_cool = NullBooleanField()
            email = EmailField(required=False)
            age = IntegerField()

        p = Person({})
        p.error_css_class = "error"
        p.required_css_class = "required"

        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li class="required error"><ul class="errorlist" id="id_name_error">
            <li>This field is required.</li></ul>
            <label class="required" for="id_name">Name:</label>
            <input type="text" name="name" id="id_name" aria-invalid="true" required
             aria-describedby="id_name_error">
            </li><li class="required">
            <label class="required" for="id_is_cool">Is cool:</label>
            <select name="is_cool" id="id_is_cool">
            <option value="unknown" selected>Unknown</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
            </select></li>
            <li><label for="id_email">Email:</label>
            <input type="email" name="email" id="id_email" maxlength="320"></li>
            <li class="required error"><ul class="errorlist" id="id_age_error">
            <li>This field is required.</li></ul>
            <label class="required" for="id_age">Age:</label>
            <input type="number" name="age" id="id_age" aria-invalid="true" required
            aria-describedby="id_age_error">
            </li>""",
        )

        self.assertHTMLEqual(
            p.as_p(),
            """
            <ul class="errorlist" id="id_name_error"><li>This field is required.</li>
            </ul><p class="required error">
            <label class="required" for="id_name">Name:</label>
            <input type="text" name="name" id="id_name" aria-invalid="true" required
            aria-describedby="id_name_error">
            </p><p class="required">
            <label class="required" for="id_is_cool">Is cool:</label>
            <select name="is_cool" id="id_is_cool">
            <option value="unknown" selected>Unknown</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
            </select></p>
            <p><label for="id_email">Email:</label>
            <input type="email" name="email" id="id_email" maxlength="320"></p>
            <ul class="errorlist" id="id_age_error"><li>This field is required.</li>
            </ul><p class="required error"><label class="required" for="id_age">
            Age:</label><input type="number" name="age" id="id_age" aria-invalid="true"
            required aria-describedby="id_age_error"></p>""",
        )

        self.assertHTMLEqual(
            p.as_table(),
            """<tr class="required error">
<th><label class="required" for="id_name">Name:</label></th>
<td><ul class="errorlist" id="id_name_error"><li>This field is required.</li></ul>
<input type="text" name="name" id="id_name" aria-invalid="true" required
aria-describedby="id_name_error"></td></tr>
<tr class="required"><th><label class="required" for="id_is_cool">Is cool:</label></th>
<td><select name="is_cool" id="id_is_cool">
<option value="unknown" selected>Unknown</option>
<option value="true">Yes</option>
<option value="false">No</option>
</select></td></tr>
<tr><th><label for="id_email">Email:</label></th><td>
<input type="email" name="email" id="id_email" maxlength="320"></td></tr>
<tr class="required error"><th><label class="required" for="id_age">Age:</label></th>
<td><ul class="errorlist" id="id_age_error"><li>This field is required.</li></ul>
<input type="number" name="age" id="id_age" aria-invalid="true" required
aria-describedby="id_age_error"></td></tr>""",
        )
        self.assertHTMLEqual(
            p.as_div(),
            '<div class="required error"><label for="id_name" class="required">Name:'
            '</label><ul class="errorlist" id="id_name_error"><li>This field is '
            'required.</li></ul><input type="text" name="name" required id="id_name" '
            'aria-invalid="true" aria-describedby="id_name_error" /></div>'
            '<div class="required"><label for="id_is_cool" class="required">Is cool:'
            '</label><select name="is_cool" id="id_is_cool">'
            '<option value="unknown" selected>Unknown</option>'
            '<option value="true">Yes</option><option value="false">No</option>'
            '</select></div><div><label for="id_email">Email:</label>'
            '<input type="email" name="email" id="id_email" maxlength="320"/></div>'
            '<div class="required error"><label for="id_age" class="required">Age:'
            '</label><ul class="errorlist" id="id_age_error"><li>This field is '
            'required.</li></ul><input type="number" name="age" required id="id_age" '
            'aria-invalid="true" aria-describedby="id_age_error" /></div>',
        )