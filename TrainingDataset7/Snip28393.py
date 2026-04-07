def test_m2m_initial_callable(self):
        """
        A callable can be provided as the initial value for an m2m field.
        """
        self.maxDiff = 1200
        self.create_basic_data()

        # Set up a callable initial value
        def formfield_for_dbfield(db_field, **kwargs):
            if db_field.name == "categories":
                kwargs["initial"] = lambda: Category.objects.order_by("name")[:2]
            return db_field.formfield(**kwargs)

        # Create a ModelForm, instantiate it, and check that the output is as
        # expected
        ModelForm = modelform_factory(
            Article,
            fields=["headline", "categories"],
            formfield_callback=formfield_for_dbfield,
        )
        form = ModelForm()
        self.assertHTMLEqual(
            form.as_ul(),
            """<li><label for="id_headline">Headline:</label>
<input id="id_headline" type="text" name="headline" maxlength="50" required></li>
<li><label for="id_categories">Categories:</label>
<select multiple name="categories" id="id_categories">
<option value="%s" selected>Entertainment</option>
<option value="%s" selected>It&#x27;s a test</option>
<option value="%s">Third test</option>
</select></li>""" % (self.c1.pk, self.c2.pk, self.c3.pk),
        )