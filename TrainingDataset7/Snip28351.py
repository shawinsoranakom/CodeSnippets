def test_orderfields2_form(self):
        class OrderFields2(forms.ModelForm):
            class Meta:
                model = Category
                fields = ["slug", "url", "name"]
                exclude = ["url"]

        self.assertEqual(list(OrderFields2.base_fields), ["slug", "name"])