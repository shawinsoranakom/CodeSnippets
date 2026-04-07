def test_iterable_model_m2m(self):
        class ColorfulItemForm(forms.ModelForm):
            class Meta:
                model = ColorfulItem
                fields = "__all__"

        color = Color.objects.create(name="Blue")
        form = ColorfulItemForm()
        self.maxDiff = 1024
        self.assertHTMLEqual(
            form.as_p(),
            """
            <p>
            <label for="id_name">Name:</label>
            <input id="id_name" type="text" name="name" maxlength="50" required></p>
            <p><label for="id_colors">Colors:</label>
            <select multiple name="colors" id="id_colors" required>
            <option value="%(blue_pk)s">Blue</option>
            </select></p>
            """ % {"blue_pk": color.pk},
        )