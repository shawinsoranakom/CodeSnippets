def test_specifying_labels(self):
        # You can specify the label for a field by using the 'label' argument
        # to a Field class. If you don't specify 'label', Django will use the
        # field name with underscores converted to spaces, and the initial
        # letter capitalized.
        class UserRegistration(Form):
            username = CharField(max_length=10, label="Your username")
            password1 = CharField(widget=PasswordInput)
            password2 = CharField(widget=PasswordInput, label="Contraseña (de nuevo)")

        p = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li>Your username:
            <input type="text" name="username" maxlength="10" required></li>
            <li>Password1: <input type="password" name="password1" required></li>
            <li>Contraseña (de nuevo):
            <input type="password" name="password2" required></li>
            """,
        )

        # Labels for as_* methods will only end in a colon if they don't end in
        # other punctuation already.
        class Questions(Form):
            q1 = CharField(label="The first question")
            q2 = CharField(label="What is your name?")
            q3 = CharField(label="The answer to life is:")
            q4 = CharField(label="Answer this question!")
            q5 = CharField(label="The last question. Period.")

        self.assertHTMLEqual(
            Questions(auto_id=False).as_p(),
            """<p>The first question: <input type="text" name="q1" required></p>
<p>What is your name? <input type="text" name="q2" required></p>
<p>The answer to life is: <input type="text" name="q3" required></p>
<p>Answer this question! <input type="text" name="q4" required></p>
<p>The last question. Period. <input type="text" name="q5" required></p>""",
        )
        self.assertHTMLEqual(
            Questions().as_p(),
            """
            <p><label for="id_q1">The first question:</label>
            <input type="text" name="q1" id="id_q1" required></p>
            <p><label for="id_q2">What is your name?</label>
            <input type="text" name="q2" id="id_q2" required></p>
            <p><label for="id_q3">The answer to life is:</label>
            <input type="text" name="q3" id="id_q3" required></p>
            <p><label for="id_q4">Answer this question!</label>
            <input type="text" name="q4" id="id_q4" required></p>
            <p><label for="id_q5">The last question. Period.</label>
            <input type="text" name="q5" id="id_q5" required></p>
            """,
        )

        # If a label is set to the empty string for a field, that field won't
        # get a label.
        class UserRegistration(Form):
            username = CharField(max_length=10, label="")
            password = CharField(widget=PasswordInput)

        p = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """<li> <input type="text" name="username" maxlength="10" required></li>
<li>Password: <input type="password" name="password" required></li>""",
        )
        p = UserRegistration(auto_id="id_%s")
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li>
            <input id="id_username" type="text" name="username" maxlength="10" required>
            </li>
            <li><label for="id_password">Password:</label>
            <input type="password" name="password" id="id_password" required></li>
            """,
        )

        # If label is None, Django will auto-create the label from the field
        # name. This is default behavior.
        class UserRegistration(Form):
            username = CharField(max_length=10, label=None)
            password = CharField(widget=PasswordInput)

        p = UserRegistration(auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            '<li>Username: <input type="text" name="username" maxlength="10" required>'
            "</li>"
            '<li>Password: <input type="password" name="password" required></li>',
        )
        p = UserRegistration(auto_id="id_%s")
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><label for="id_username">Username:</label>
<input id="id_username" type="text" name="username" maxlength="10" required></li>
<li><label for="id_password">Password:</label>
<input type="password" name="password" id="id_password" required></li>""",
        )