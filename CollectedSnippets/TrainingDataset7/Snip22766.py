def test_widget_output(self):
        # Any Field can have a Widget class passed to its constructor:
        class ContactForm(Form):
            subject = CharField()
            message = CharField(widget=Textarea)

        f = ContactForm(auto_id=False)
        self.assertHTMLEqual(
            str(f["subject"]), '<input type="text" name="subject" required>'
        )
        self.assertHTMLEqual(
            str(f["message"]),
            '<textarea name="message" rows="10" cols="40" required></textarea>',
        )

        # as_textarea(), as_text() and as_hidden() are shortcuts for changing
        # the output widget type:
        self.assertHTMLEqual(
            f["subject"].as_textarea(),
            '<textarea name="subject" rows="10" cols="40" required></textarea>',
        )
        self.assertHTMLEqual(
            f["message"].as_text(), '<input type="text" name="message" required>'
        )
        self.assertHTMLEqual(
            f["message"].as_hidden(), '<input type="hidden" name="message">'
        )

        # The 'widget' parameter to a Field can also be an instance:
        class ContactForm(Form):
            subject = CharField()
            message = CharField(widget=Textarea(attrs={"rows": 80, "cols": 20}))

        f = ContactForm(auto_id=False)
        self.assertHTMLEqual(
            str(f["message"]),
            '<textarea name="message" rows="80" cols="20" required></textarea>',
        )

        # Instance-level attrs are *not* carried over to as_textarea(),
        # as_text() and as_hidden():
        self.assertHTMLEqual(
            f["message"].as_text(), '<input type="text" name="message" required>'
        )
        f = ContactForm({"subject": "Hello", "message": "I love you."}, auto_id=False)
        self.assertHTMLEqual(
            f["subject"].as_textarea(),
            '<textarea rows="10" cols="40" name="subject" required>Hello</textarea>',
        )
        self.assertHTMLEqual(
            f["message"].as_text(),
            '<input type="text" name="message" value="I love you." required>',
        )
        self.assertHTMLEqual(
            f["message"].as_hidden(),
            '<input type="hidden" name="message" value="I love you.">',
        )