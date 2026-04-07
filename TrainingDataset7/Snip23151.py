def test_validation_error(self):
        ###################
        # ValidationError #
        ###################

        # Can take a string.
        self.assertHTMLEqual(
            str(ErrorList(ValidationError("There was an error.").messages)),
            '<ul class="errorlist"><li>There was an error.</li></ul>',
        )
        # Can take a Unicode string.
        self.assertHTMLEqual(
            str(ErrorList(ValidationError("Not \u03c0.").messages)),
            '<ul class="errorlist"><li>Not π.</li></ul>',
        )
        # Can take a lazy string.
        self.assertHTMLEqual(
            str(ErrorList(ValidationError(gettext_lazy("Error.")).messages)),
            '<ul class="errorlist"><li>Error.</li></ul>',
        )
        # Can take a list.
        self.assertHTMLEqual(
            str(ErrorList(ValidationError(["Error one.", "Error two."]).messages)),
            '<ul class="errorlist"><li>Error one.</li><li>Error two.</li></ul>',
        )
        # Can take a dict.
        self.assertHTMLEqual(
            str(
                ErrorList(
                    sorted(
                        ValidationError(
                            {"error_1": "1. Error one.", "error_2": "2. Error two."}
                        ).messages
                    )
                )
            ),
            '<ul class="errorlist"><li>1. Error one.</li><li>2. Error two.</li></ul>',
        )
        # Can take a mixture in a list.
        self.assertHTMLEqual(
            str(
                ErrorList(
                    sorted(
                        ValidationError(
                            [
                                "1. First error.",
                                "2. Not \u03c0.",
                                gettext_lazy("3. Error."),
                                {
                                    "error_1": "4. First dict error.",
                                    "error_2": "5. Second dict error.",
                                },
                            ]
                        ).messages
                    )
                )
            ),
            '<ul class="errorlist">'
            "<li>1. First error.</li>"
            "<li>2. Not π.</li>"
            "<li>3. Error.</li>"
            "<li>4. First dict error.</li>"
            "<li>5. Second dict error.</li>"
            "</ul>",
        )

        class VeryBadError:
            def __str__(self):
                return "A very bad error."

        # Can take a non-string.
        self.assertHTMLEqual(
            str(ErrorList(ValidationError(VeryBadError()).messages)),
            '<ul class="errorlist"><li>A very bad error.</li></ul>',
        )

        # Escapes non-safe input but not input marked safe.
        example = 'Example of link: <a href="http://www.example.com/">example</a>'
        self.assertHTMLEqual(
            str(ErrorList([example])),
            '<ul class="errorlist"><li>Example of link: '
            "&lt;a href=&quot;http://www.example.com/&quot;&gt;example&lt;/a&gt;"
            "</li></ul>",
        )
        self.assertHTMLEqual(
            str(ErrorList([mark_safe(example)])),
            '<ul class="errorlist"><li>Example of link: '
            '<a href="http://www.example.com/">example</a></li></ul>',
        )
        self.assertHTMLEqual(
            str(ErrorDict({"name": example})),
            '<ul class="errorlist"><li>nameExample of link: '
            "&lt;a href=&quot;http://www.example.com/&quot;&gt;example&lt;/a&gt;"
            "</li></ul>",
        )
        self.assertHTMLEqual(
            str(ErrorDict({"name": mark_safe(example)})),
            '<ul class="errorlist"><li>nameExample of link: '
            '<a href="http://www.example.com/">example</a></li></ul>',
        )