def test_list_display_method_same_name_as_reverse_accessor(self):
        """
        Should be able to use a ModelAdmin method in list_display that has the
        same name as a reverse model field ("sketch" in this case).
        """
        actor = Actor.objects.create(name="Palin", age=27)
        Inquisition.objects.create(expected=True, leader=actor, country="England")
        response = self.client.get(reverse("admin:admin_views_inquisition_changelist"))
        self.assertContains(response, "list-display-sketch")