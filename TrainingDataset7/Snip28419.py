def test_onetoonefield(self):
        class WriterProfileForm(forms.ModelForm):
            class Meta:
                # WriterProfile has a OneToOneField to Writer
                model = WriterProfile
                fields = "__all__"

        self.w_royko = Writer.objects.create(name="Mike Royko")
        self.w_woodward = Writer.objects.create(name="Bob Woodward")

        form = WriterProfileForm()
        self.assertHTMLEqual(
            form.as_p(),
            """
            <p><label for="id_writer">Writer:</label>
            <select name="writer" id="id_writer" required>
            <option value="" selected>---------</option>
            <option value="%s">Bob Woodward</option>
            <option value="%s">Mike Royko</option>
            </select></p>
            <p><label for="id_age">Age:</label>
            <input type="number" name="age" id="id_age" min="0" required></p>
            """
            % (
                self.w_woodward.pk,
                self.w_royko.pk,
            ),
        )

        data = {
            "writer": str(self.w_woodward.pk),
            "age": "65",
        }
        form = WriterProfileForm(data)
        instance = form.save()
        self.assertEqual(str(instance), "Bob Woodward is 65")

        form = WriterProfileForm(instance=instance)
        self.assertHTMLEqual(
            form.as_p(),
            """
            <p><label for="id_writer">Writer:</label>
            <select name="writer" id="id_writer" required>
            <option value="">---------</option>
            <option value="%s" selected>Bob Woodward</option>
            <option value="%s">Mike Royko</option>
            </select></p>
            <p><label for="id_age">Age:</label>
            <input type="number" name="age" value="65" id="id_age" min="0" required>
            </p>"""
            % (
                self.w_woodward.pk,
                self.w_royko.pk,
            ),
        )