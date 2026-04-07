def check_html(
        self, widget, name, value, html="", attrs=None, strict=False, **kwargs
    ):
        assertEqual = self.assertEqual if strict else self.assertHTMLEqual
        if self.jinja2_renderer:
            output = widget.render(
                name, value, attrs=attrs, renderer=self.jinja2_renderer, **kwargs
            )
            # Django escapes quotes with '&quot;' while Jinja2 uses '&#34;'.
            output = output.replace("&#34;", "&quot;")
            # Django escapes single quotes with '&#x27;' while Jinja2 uses
            # '&#39;'.
            output = output.replace("&#39;", "&#x27;")
            assertEqual(output, html)

        output = widget.render(
            name, value, attrs=attrs, renderer=self.django_renderer, **kwargs
        )
        assertEqual(output, html)