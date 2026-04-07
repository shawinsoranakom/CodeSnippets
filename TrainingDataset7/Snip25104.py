def test_localized_as_text_as_hidden_input(self):
        """
        Form input with 'as_hidden' or 'as_text' is correctly localized.
        """
        self.maxDiff = 1200

        with translation.override("de-at", deactivate=True):
            template = Template(
                "{% load l10n %}{{ form.date_added }}; {{ form.cents_paid }}"
            )
            template_as_text = Template(
                "{% load l10n %}"
                "{{ form.date_added.as_text }}; {{ form.cents_paid.as_text }}"
            )
            template_as_hidden = Template(
                "{% load l10n %}"
                "{{ form.date_added.as_hidden }}; {{ form.cents_paid.as_hidden }}"
            )
            form = CompanyForm(
                {
                    "name": "acme",
                    "date_added": datetime.datetime(2009, 12, 31, 6, 0, 0),
                    "cents_paid": decimal.Decimal("59.47"),
                    "products_delivered": 12000,
                }
            )
            context = Context({"form": form})
            self.assertTrue(form.is_valid())

            self.assertHTMLEqual(
                template.render(context),
                '<input id="id_date_added" name="date_added" type="text" '
                'value="31.12.2009 06:00:00" required>;'
                '<input id="id_cents_paid" name="cents_paid" type="text" value="59,47" '
                "required>",
            )
            self.assertHTMLEqual(
                template_as_text.render(context),
                '<input id="id_date_added" name="date_added" type="text" '
                'value="31.12.2009 06:00:00" required>;'
                '<input id="id_cents_paid" name="cents_paid" type="text" value="59,47" '
                "required>",
            )
            self.assertHTMLEqual(
                template_as_hidden.render(context),
                '<input id="id_date_added" name="date_added" type="hidden" '
                'value="31.12.2009 06:00:00">;'
                '<input id="id_cents_paid" name="cents_paid" type="hidden" '
                'value="59,47">',
            )