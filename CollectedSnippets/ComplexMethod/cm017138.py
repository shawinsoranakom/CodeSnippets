def test_inline_headings(self):
        response = self.client.get(reverse("admin:admin_inlines_photographer_add"))
        # Page main title.
        self.assertContains(response, "<h1>Add photographer</h1>", html=True)

        # Headings for the toplevel fieldsets. The first one has no name.
        self.assertContains(response, '<fieldset class="module aligned ">')
        # The second and third have the same "Advanced options" name, but the
        # second one has the "collapse" class.
        for x, classes in ((1, ""), (2, "collapse")):
            heading_id = f"fieldset-0-{x}-heading"
            with self.subTest(heading_id=heading_id):
                self.assertContains(
                    response,
                    f'<fieldset class="module aligned {classes}" '
                    f'aria-labelledby="{heading_id}">',
                )
                self.assertContains(
                    response,
                    f'<h2 id="{heading_id}" class="fieldset-heading">'
                    "Advanced options</h2>",
                )
                self.assertContains(response, f'id="{heading_id}"', count=1)

        # Headings and subheadings for all the inlines.
        for inline_admin_formset in response.context["inline_admin_formsets"]:
            prefix = inline_admin_formset.formset.prefix
            heading_id = f"{prefix}-heading"
            formset_heading = (
                f'<h2 id="{heading_id}" class="inline-heading">Photos</h2>'
            )
            self.assertContains(response, formset_heading, html=True)
            self.assertContains(response, f'id="{heading_id}"', count=1)

            # If this is a TabularInline, do not make further asserts since
            # fieldsets are not shown as such in this table layout.
            if "tabular" in inline_admin_formset.opts.template:
                continue

            if "collapse" in inline_admin_formset.classes:
                formset_heading = f"<summary>{formset_heading}</summary>"
                self.assertContains(response, formset_heading, html=True, count=1)

            # Headings for every formset (the amount depends on `extra`).
            for y, inline_admin_form in enumerate(inline_admin_formset):
                y_plus_one = y + 1
                form_heading = (
                    f'<h3><b>Photo:</b> <span class="inline_label">#{y_plus_one}</span>'
                    "</h3>"
                )
                self.assertContains(response, form_heading, html=True)

                # Every fieldset defined for an inline's form.
                for z, fieldset in enumerate(inline_admin_form):
                    if fieldset.name:
                        heading_id = f"{prefix}-{y}-{z}-heading"
                        self.assertContains(
                            response,
                            f'<fieldset class="module aligned {fieldset.classes}" '
                            f'aria-labelledby="{heading_id}">',
                        )
                        fieldset_heading = (
                            f'<h4 id="{heading_id}" class="fieldset-heading">'
                            f"Details</h4>"
                        )
                        self.assertContains(response, fieldset_heading)
                        if "collapse" in fieldset.classes:
                            self.assertContains(
                                response,
                                f"<summary>{fieldset_heading}</summary>",
                                html=True,
                            )
                        self.assertContains(response, f'id="{heading_id}"', count=1)

                    else:
                        fieldset_html = (
                            f'<fieldset class="module aligned {fieldset.classes}">'
                        )
                        self.assertContains(response, fieldset_html)