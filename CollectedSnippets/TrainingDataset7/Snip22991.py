def test_formsets_with_ordering_custom_widget(self):
        class OrderingAttributeFormSet(BaseFormSet):
            ordering_widget = HiddenInput

        class OrderingMethodFormSet(BaseFormSet):
            def get_ordering_widget(self):
                return HiddenInput(attrs={"class": "ordering"})

        tests = (
            (OrderingAttributeFormSet, '<input type="hidden" name="form-0-ORDER">'),
            (
                OrderingMethodFormSet,
                '<input class="ordering" type="hidden" name="form-0-ORDER">',
            ),
        )
        for formset_class, order_html in tests:
            with self.subTest(formset_class=formset_class.__name__):
                ArticleFormSet = formset_factory(
                    ArticleForm, formset=formset_class, can_order=True
                )
                formset = ArticleFormSet(auto_id=False)
                self.assertHTMLEqual(
                    "\n".join(form.as_ul() for form in formset.forms),
                    (
                        '<li>Title: <input type="text" name="form-0-title"></li>'
                        '<li>Pub date: <input type="text" name="form-0-pub_date">'
                        "%s</li>" % order_html
                    ),
                )