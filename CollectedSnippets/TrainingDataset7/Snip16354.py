def test_enable_zooming_on_mobile(self):
        response = self.client.get(reverse("admin:index"))
        self.assertContains(
            response,
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        )