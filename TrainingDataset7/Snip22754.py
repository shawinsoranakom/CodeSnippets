def test_empty_dict(self):
        # Empty dictionaries are valid, too.
        p = Person({})
        self.assertTrue(p.is_bound)
        self.assertEqual(p.errors["first_name"], ["This field is required."])
        self.assertEqual(p.errors["last_name"], ["This field is required."])
        self.assertEqual(p.errors["birthday"], ["This field is required."])
        self.assertFalse(p.is_valid())
        self.assertEqual(p.cleaned_data, {})
        self.assertHTMLEqual(
            str(p),
            '<div><label for="id_first_name">First name:</label>'
            '<ul class="errorlist" id="id_first_name_error"><li>This field is required.'
            '</li></ul><input type="text" name="first_name" aria-invalid="true" '
            'required id="id_first_name" aria-describedby="id_first_name_error"></div>'
            '<div><label for="id_last_name">Last name:</label>'
            '<ul class="errorlist" id="id_last_name_error"><li>This field is required.'
            '</li></ul><input type="text" name="last_name" aria-invalid="true" '
            'required id="id_last_name" aria-describedby="id_last_name_error"></div>'
            '<div><label for="id_birthday">Birthday:</label>'
            '<ul class="errorlist" id="id_birthday_error"><li>This field is required.'
            '</li></ul><input type="text" name="birthday" aria-invalid="true" required '
            'id="id_birthday" aria-describedby="id_birthday_error"></div>',
        )
        self.assertHTMLEqual(
            p.as_table(),
            """<tr><th><label for="id_first_name">First name:</label></th><td>
<ul class="errorlist" id="id_first_name_error"><li>This field is required.</li></ul>
<input type="text" name="first_name" id="id_first_name" aria-invalid="true" required
aria-describedby="id_first_name_error">
</td></tr><tr><th><label for="id_last_name">Last name:</label></th>
<td><ul class="errorlist" id="id_last_name_error"><li>This field is required.</li></ul>
<input type="text" name="last_name" id="id_last_name" aria-invalid="true" required
aria-describedby="id_last_name_error">
</td></tr><tr><th><label for="id_birthday">Birthday:</label></th>
<td><ul class="errorlist" id="id_birthday_error"><li>This field is required.</li></ul>
<input type="text" name="birthday" id="id_birthday" aria-invalid="true" required
aria-describedby="id_birthday_error">
</td></tr>""",
        )
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><ul class="errorlist" id="id_first_name_error">
<li>This field is required.</li></ul>
<label for="id_first_name">First name:</label>
<input type="text" name="first_name" id="id_first_name" aria-invalid="true" required
aria-describedby="id_first_name_error">
</li><li><ul class="errorlist" id="id_last_name_error"><li>This field is required.</li>
</ul><label for="id_last_name">Last name:</label>
<input type="text" name="last_name" id="id_last_name" aria-invalid="true" required
aria-describedby="id_last_name_error">
</li><li><ul class="errorlist" id="id_birthday_error"><li>This field is required.</li>
</ul><label for="id_birthday">Birthday:</label>
<input type="text" name="birthday" id="id_birthday" aria-invalid="true" required
aria-describedby="id_birthday_error">
</li>""",
        )
        self.assertHTMLEqual(
            p.as_p(),
            """<ul class="errorlist" id="id_first_name_error"><li>
This field is required.</li></ul>
<p><label for="id_first_name">First name:</label>
<input type="text" name="first_name" id="id_first_name" aria-invalid="true" required
aria-describedby="id_first_name_error">
</p><ul class="errorlist" id="id_last_name_error"><li>This field is required.</li></ul>
<p><label for="id_last_name">Last name:</label>
<input type="text" name="last_name" id="id_last_name" aria-invalid="true" required
aria-describedby="id_last_name_error">
</p><ul class="errorlist" id="id_birthday_error"><li>This field is required.</li></ul>
<p><label for="id_birthday">Birthday:</label>
<input type="text" name="birthday" id="id_birthday" aria-invalid="true" required
aria-describedby="id_birthday_error">
</p>""",
        )
        self.assertHTMLEqual(
            p.as_div(),
            '<div><label for="id_first_name">First name:</label>'
            '<ul class="errorlist" id="id_first_name_error"><li>This field is required.'
            '</li></ul><input type="text" name="first_name" aria-invalid="true" '
            'required id="id_first_name" aria-describedby="id_first_name_error"></div>'
            '<div><label for="id_last_name">Last name:</label>'
            '<ul class="errorlist" id="id_last_name_error"><li>This field is required.'
            '</li></ul><input type="text" name="last_name" aria-invalid="true" '
            'required id="id_last_name" aria-describedby="id_last_name_error"></div>'
            '<div><label for="id_birthday">Birthday:</label>'
            '<ul class="errorlist" id="id_birthday_error"><li>This field is required.'
            '</li></ul><input type="text" name="birthday" aria-invalid="true" required '
            'id="id_birthday" aria-describedby="id_birthday_error"></div>',
        )