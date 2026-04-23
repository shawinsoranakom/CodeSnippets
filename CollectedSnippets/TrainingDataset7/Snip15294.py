def test_post_url_continue(self):
        """
        The ModelAdmin.response_add()'s parameter `post_url_continue` controls
        the redirection after an object has been created.
        """
        post_data = {"name": "SuperFast", "_continue": "1"}
        self.assertEqual(Car.objects.count(), 0)
        response = self.client.post(
            reverse("admin_custom_urls:admin_custom_urls_car_add"), post_data
        )
        cars = Car.objects.all()
        self.assertEqual(len(cars), 1)
        self.assertRedirects(
            response,
            reverse(
                "admin_custom_urls:admin_custom_urls_car_history", args=[cars[0].pk]
            ),
        )