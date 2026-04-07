def test_templates_with_forms(self):
        class UserRegistration(Form):
            username = CharField(
                max_length=10,
                help_text=("Good luck picking a username that doesn't already exist."),
            )
            password1 = CharField(widget=PasswordInput)
            password2 = CharField(widget=PasswordInput)

            def clean(self):
                if (
                    self.cleaned_data.get("password1")
                    and self.cleaned_data.get("password2")
                    and self.cleaned_data["password1"] != self.cleaned_data["password2"]
                ):
                    raise ValidationError("Please make sure your passwords match.")
                return self.cleaned_data

        # There is full flexibility in displaying form fields in a template.
        # Just pass a Form instance to the template, and use "dot" access to
        # refer to individual fields. However, this flexibility comes with the
        # responsibility of displaying all the errors, including any that might
        # not be associated with a particular field.
        t = Template(
            "<form>"
            "{{ form.username.errors.as_ul }}"
            "<p><label>Your username: {{ form.username }}</label></p>"
            "{{ form.password1.errors.as_ul }}"
            "<p><label>Password: {{ form.password1 }}</label></p>"
            "{{ form.password2.errors.as_ul }}"
            "<p><label>Password (again): {{ form.password2 }}</label></p>"
            '<input type="submit" required>'
            "</form>"
        )
        f = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            "<form>"
            "<p><label>Your username: "
            '<input type="text" name="username" maxlength="10" required></label></p>'
            "<p><label>Password: "
            '<input type="password" name="password1" required></label></p>'
            "<p><label>Password (again): "
            '<input type="password" name="password2" required></label></p>'
            '<input type="submit" required>'
            "</form>",
        )
        f = UserRegistration({"username": "django"}, auto_id=False)
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            "<form>"
            "<p><label>Your username: "
            '<input type="text" name="username" value="django" maxlength="10" required>'
            "</label></p>"
            '<ul class="errorlist"><li>This field is required.</li></ul><p>'
            "<label>Password: "
            '<input type="password" name="password1" aria-invalid="true" required>'
            "</label></p>"
            '<ul class="errorlist"><li>This field is required.</li></ul>'
            "<p><label>Password (again): "
            '<input type="password" name="password2" aria-invalid="true" required>'
            "</label></p>"
            '<input type="submit" required>'
            "</form>",
        )
        # Use form.[field].label to output a field's label. 'label' for a field
        # can by specified by using the 'label' argument to a Field class. If
        # 'label' is not specified, Django will use the field name with
        # underscores converted to spaces, and the initial letter capitalized.
        t = Template(
            "<form>"
            "<p><label>{{ form.username.label }}: {{ form.username }}</label></p>"
            "<p><label>{{ form.password1.label }}: {{ form.password1 }}</label></p>"
            "<p><label>{{ form.password2.label }}: {{ form.password2 }}</label></p>"
            '<input type="submit" required>'
            "</form>"
        )
        f = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            "<form>"
            "<p><label>Username: "
            '<input type="text" name="username" maxlength="10" required></label></p>'
            "<p><label>Password1: "
            '<input type="password" name="password1" required></label></p>'
            "<p><label>Password2: "
            '<input type="password" name="password2" required></label></p>'
            '<input type="submit" required>'
            "</form>",
        )
        # Use form.[field].label_tag to output a field's label with a <label>
        # tag wrapped around it, but *only* if the given field has an "id"
        # attribute. Recall from above that passing the "auto_id" argument to a
        # Form gives each field an "id" attribute.
        t = Template(
            "<form>"
            "<p>{{ form.username.label_tag }} {{ form.username }}"
            '<span {% if form.username.id_for_label %}id="'
            '{{ form.username.id_for_label }}_helptext"{% endif %}>'
            "{{ form.username.help_text}}</span></p>"
            "<p>{{ form.password1.label_tag }} {{ form.password1 }}</p>"
            "<p>{{ form.password2.label_tag }} {{ form.password2 }}</p>"
            '<input type="submit" required>'
            "</form>"
        )
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            "<form>"
            "<p>Username: "
            '<input type="text" name="username" maxlength="10" required>'
            "<span>Good luck picking a username that doesn't already exist.</span></p>"
            '<p>Password1: <input type="password" name="password1" required></p>'
            '<p>Password2: <input type="password" name="password2" required></p>'
            '<input type="submit" required>'
            "</form>",
        )
        f = UserRegistration(auto_id="id_%s")
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            "<form>"
            '<p><label for="id_username">Username:</label>'
            '<input id="id_username" type="text" name="username" maxlength="10" '
            'aria-describedby="id_username_helptext" required>'
            '<span id="id_username_helptext">'
            "Good luck picking a username that doesn't already exist.</span></p>"
            '<p><label for="id_password1">Password1:</label>'
            '<input type="password" name="password1" id="id_password1" required></p>'
            '<p><label for="id_password2">Password2:</label>'
            '<input type="password" name="password2" id="id_password2" required></p>'
            '<input type="submit" required>'
            "</form>",
        )
        # Use form.[field].legend_tag to output a field's label with a <legend>
        # tag wrapped around it, but *only* if the given field has an "id"
        # attribute. Recall from above that passing the "auto_id" argument to a
        # Form gives each field an "id" attribute.
        t = Template(
            "<form>"
            "<p>{{ form.username.legend_tag }} {{ form.username }}</p>"
            "<p>{{ form.password1.legend_tag }} {{ form.password1 }}</p>"
            "<p>{{ form.password2.legend_tag }} {{ form.password2 }}</p>"
            '<input type="submit" required>'
            "</form>"
        )
        f = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            "<form>"
            "<p>Username: "
            '<input type="text" name="username" maxlength="10" required></p>'
            '<p>Password1: <input type="password" name="password1" required></p>'
            '<p>Password2: <input type="password" name="password2" required></p>'
            '<input type="submit" required>'
            "</form>",
        )
        f = UserRegistration(auto_id="id_%s")
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            "<form>"
            "<p><legend>Username:</legend>"
            '<input id="id_username" type="text" name="username" maxlength="10" '
            'aria-describedby="id_username_helptext" required></p>'
            "<p><legend>Password1:</legend>"
            '<input type="password" name="password1" id="id_password1" required></p>'
            "<p><legend>Password2:</legend>"
            '<input type="password" name="password2" id="id_password2" required></p>'
            '<input type="submit" required>'
            "</form>",
        )
        # Use form.[field].help_text to output a field's help text. If the
        # given field does not have help text, nothing will be output.
        t = Template(
            "<form>"
            "<p>{{ form.username.label_tag }} {{ form.username }}<br>"
            "{{ form.username.help_text }}</p>"
            "<p>{{ form.password1.label_tag }} {{ form.password1 }}</p>"
            "<p>{{ form.password2.label_tag }} {{ form.password2 }}</p>"
            '<input type="submit" required>'
            "</form>"
        )
        f = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            "<form>"
            "<p>Username: "
            '<input type="text" name="username" maxlength="10" required><br>'
            "Good luck picking a username that doesn&#x27;t already exist.</p>"
            '<p>Password1: <input type="password" name="password1" required></p>'
            '<p>Password2: <input type="password" name="password2" required></p>'
            '<input type="submit" required>'
            "</form>",
        )
        self.assertEqual(
            Template("{{ form.password1.help_text }}").render(Context({"form": f})),
            "",
        )
        # To display the errors that aren't associated with a particular field
        # e.g. the errors caused by Form.clean() -- use
        # {{ form.non_field_errors }} in the template. If used on its own, it
        # is displayed as a <ul> (or an empty string, if the list of errors is
        # empty).
        t = Template(
            "<form>"
            "{{ form.username.errors.as_ul }}"
            "<p><label>Your username: {{ form.username }}</label></p>"
            "{{ form.password1.errors.as_ul }}"
            "<p><label>Password: {{ form.password1 }}</label></p>"
            "{{ form.password2.errors.as_ul }}"
            "<p><label>Password (again): {{ form.password2 }}</label></p>"
            '<input type="submit" required>'
            "</form>"
        )
        f = UserRegistration(
            {"username": "django", "password1": "foo", "password2": "bar"},
            auto_id=False,
        )
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            "<form>"
            "<p><label>Your username: "
            '<input type="text" name="username" value="django" maxlength="10" required>'
            "</label></p>"
            "<p><label>Password: "
            '<input type="password" name="password1" required></label></p>'
            "<p><label>Password (again): "
            '<input type="password" name="password2" required></label></p>'
            '<input type="submit" required>'
            "</form>",
        )
        t = Template(
            "<form>"
            "{{ form.non_field_errors }}"
            "{{ form.username.errors.as_ul }}"
            "<p><label>Your username: {{ form.username }}</label></p>"
            "{{ form.password1.errors.as_ul }}"
            "<p><label>Password: {{ form.password1 }}</label></p>"
            "{{ form.password2.errors.as_ul }}"
            "<p><label>Password (again): {{ form.password2 }}</label></p>"
            '<input type="submit" required>'
            "</form>"
        )
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            "<form>"
            '<ul class="errorlist nonfield">'
            "<li>Please make sure your passwords match.</li></ul>"
            "<p><label>Your username: "
            '<input type="text" name="username" value="django" maxlength="10" required>'
            "</label></p>"
            "<p><label>Password: "
            '<input type="password" name="password1" required></label></p>'
            "<p><label>Password (again): "
            '<input type="password" name="password2" required></label></p>'
            '<input type="submit" required>'
            "</form>",
        )