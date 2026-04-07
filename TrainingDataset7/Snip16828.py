def test_changelist_ForeignKey(self):
        response = self.client.get(reverse("admin:admin_widgets_car_changelist"))
        self.assertContains(response, "/auth/user/add/")