def test_escaping(self):
        # Validation errors are HTML-escaped when output as HTML.
        class EscapingForm(Form):
            special_name = CharField(label="<em>Special</em> Field")
            special_safe_name = CharField(label=mark_safe("<em>Special</em> Field"))

            def clean_special_name(self):
                raise ValidationError(
                    "Something's wrong with '%s'" % self.cleaned_data["special_name"]
                )

            def clean_special_safe_name(self):
                raise ValidationError(
                    mark_safe(
                        "'<b>%s</b>' is a safe string"
                        % self.cleaned_data["special_safe_name"]
                    )
                )

        f = EscapingForm(
            {
                "special_name": "Nothing to escape",
                "special_safe_name": "Nothing to escape",
            },
            auto_id=False,
        )
        self.assertHTMLEqual(
            f.as_table(),
            """
            <tr><th>&lt;em&gt;Special&lt;/em&gt; Field:</th><td>
            <ul class="errorlist">
            <li>Something&#x27;s wrong with &#x27;Nothing to escape&#x27;</li></ul>
            <input type="text" name="special_name" value="Nothing to escape"
            aria-invalid="true" required></td></tr>
            <tr><th><em>Special</em> Field:</th><td>
            <ul class="errorlist">
            <li>'<b>Nothing to escape</b>' is a safe string</li></ul>
            <input type="text" name="special_safe_name" value="Nothing to escape"
            aria-invalid="true" required></td></tr>
            """,
        )
        f = EscapingForm(
            {
                "special_name": "Should escape < & > and <script>alert('xss')</script>",
                "special_safe_name": "<i>Do not escape</i>",
            },
            auto_id=False,
        )
        self.assertHTMLEqual(
            f.as_table(),
            "<tr><th>&lt;em&gt;Special&lt;/em&gt; Field:</th><td>"
            '<ul class="errorlist"><li>'
            "Something&#x27;s wrong with &#x27;Should escape &lt; &amp; &gt; and "
            "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;&#x27;</li></ul>"
            '<input type="text" name="special_name" value="Should escape &lt; &amp; '
            '&gt; and &lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" '
            'aria-invalid="true" required></td></tr>'
            "<tr><th><em>Special</em> Field:</th><td>"
            '<ul class="errorlist">'
            "<li>'<b><i>Do not escape</i></b>' is a safe string</li></ul>"
            '<input type="text" name="special_safe_name" '
            'value="&lt;i&gt;Do not escape&lt;/i&gt;" aria-invalid="true" required>'
            "</td></tr>",
        )