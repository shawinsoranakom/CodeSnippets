def test_render_options_fk_as_pk(self):
        beatles = Band.objects.create(name="The Beatles", style="rock")
        rubber_soul = Album.objects.create(name="Rubber Soul", band=beatles)
        release_event = ReleaseEvent.objects.create(
            name="Test Target", album=rubber_soul
        )
        form = VideoStreamForm(initial={"release_event": release_event.pk})
        output = form.as_table()
        selected_option = (
            '<option value="%s" selected>Test Target</option>' % release_event.pk
        )
        self.assertIn(selected_option, output)