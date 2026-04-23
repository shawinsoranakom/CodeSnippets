def test_custom_form(self):
        """
        model_formset_factory() respects fields and exclude parameters of a
        custom form.
        """

        class PostForm1(forms.ModelForm):
            class Meta:
                model = Post
                fields = ("title", "posted")

        class PostForm2(forms.ModelForm):
            class Meta:
                model = Post
                exclude = ("subtitle",)

        PostFormSet = modelformset_factory(Post, form=PostForm1)
        formset = PostFormSet()
        self.assertNotIn("subtitle", formset.forms[0].fields)

        PostFormSet = modelformset_factory(Post, form=PostForm2)
        formset = PostFormSet()
        self.assertNotIn("subtitle", formset.forms[0].fields)