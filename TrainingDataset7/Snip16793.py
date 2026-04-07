def test_render_options(self):
        beatles = Band.objects.create(name="The Beatles", style="rock")
        who = Band.objects.create(name="The Who", style="rock")
        # With 'band', a ForeignKey.
        form = AlbumForm(initial={"band": beatles.uuid})
        output = form.as_table()
        selected_option = (
            '<option value="%s" selected>The Beatles</option>' % beatles.uuid
        )
        option = '<option value="%s">The Who</option>' % who.uuid
        self.assertIn(selected_option, output)
        self.assertNotIn(option, output)
        # With 'featuring', a ManyToManyField.
        form = AlbumForm(initial={"featuring": [beatles.pk, who.pk]})
        output = form.as_table()
        selected_option = (
            '<option value="%s" selected>The Beatles</option>' % beatles.pk
        )
        option = '<option value="%s" selected>The Who</option>' % who.pk
        self.assertIn(selected_option, output)
        self.assertIn(option, output)