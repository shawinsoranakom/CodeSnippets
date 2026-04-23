def test_change_view_logs_m2m_field_changes(self):
        """Changes to ManyToManyFields are included in the object's history."""
        pizza = ReadablePizza.objects.create(name="Cheese")
        cheese = Topping.objects.create(name="cheese")
        post_data = {"name": pizza.name, "toppings": [cheese.pk]}
        response = self.client.post(
            reverse("admin:admin_views_readablepizza_change", args=(pizza.pk,)),
            post_data,
        )
        self.assertRedirects(
            response, reverse("admin:admin_views_readablepizza_changelist")
        )
        pizza_ctype = ContentType.objects.get_for_model(
            ReadablePizza, for_concrete_model=False
        )
        log = LogEntry.objects.filter(
            content_type=pizza_ctype, object_id=pizza.pk
        ).first()
        self.assertEqual(log.get_change_message(), "Changed Toppings.")