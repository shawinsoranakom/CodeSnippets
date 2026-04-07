def test_nonexistent_target_id(self):
        band = Band.objects.create(name="Bogey Blues")
        pk = band.pk
        band.delete()
        post_data = {
            "main_band": str(pk),
        }
        # Try posting with a nonexistent pk in a raw id field: this
        # should result in an error message, not a server exception.
        response = self.client.post(reverse("admin:admin_widgets_event_add"), post_data)
        self.assertContains(
            response,
            "Select a valid choice. That choice is not one of the available choices.",
        )