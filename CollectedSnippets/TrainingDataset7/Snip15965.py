def test_label_for_field_form_argument(self):
        class ArticleForm(forms.ModelForm):
            extra_form_field = forms.BooleanField()

            class Meta:
                fields = "__all__"
                model = Article

        self.assertEqual(
            label_for_field("extra_form_field", Article, form=ArticleForm()),
            "Extra form field",
        )
        msg = "Unable to lookup 'nonexistent' on Article or ArticleForm"
        with self.assertRaisesMessage(AttributeError, msg):
            label_for_field("nonexistent", Article, form=ArticleForm())