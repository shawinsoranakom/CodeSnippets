def test_custom_form_fields(self):
        # Here, we define a custom ModelForm. Because it happens to have the
        # same fields as the Category model, we can just call the form's save()
        # to apply its changes to an existing Category instance.
        class ShortCategory(forms.ModelForm):
            name = forms.CharField(max_length=5)
            slug = forms.CharField(max_length=5)
            url = forms.CharField(max_length=3)

            class Meta:
                model = Category
                fields = "__all__"

        cat = Category.objects.create(name="Third test")
        form = ShortCategory(
            {"name": "Third", "slug": "third", "url": "3rd"}, instance=cat
        )
        self.assertEqual(form.save().name, "Third")
        self.assertEqual(Category.objects.get(id=cat.id).name, "Third")