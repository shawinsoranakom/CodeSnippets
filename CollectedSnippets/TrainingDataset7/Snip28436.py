def test_modelform_non_editable_field(self):
        """
        When explicitly including a non-editable field in a ModelForm, the
        error message should be explicit.
        """
        # 'created', non-editable, is excluded by default
        self.assertNotIn("created", ArticleForm().fields)

        msg = (
            "'created' cannot be specified for Article model form as it is a "
            "non-editable field"
        )
        with self.assertRaisesMessage(FieldError, msg):

            class InvalidArticleForm(forms.ModelForm):
                class Meta:
                    model = Article
                    fields = ("headline", "created")