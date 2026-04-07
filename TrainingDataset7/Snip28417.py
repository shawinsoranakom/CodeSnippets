def test_modelform_onetoonefield(self):
        class ImprovedArticleForm(forms.ModelForm):
            class Meta:
                model = ImprovedArticle
                fields = "__all__"

        class ImprovedArticleWithParentLinkForm(forms.ModelForm):
            class Meta:
                model = ImprovedArticleWithParentLink
                fields = "__all__"

        self.assertEqual(list(ImprovedArticleForm.base_fields), ["article"])
        self.assertEqual(list(ImprovedArticleWithParentLinkForm.base_fields), [])