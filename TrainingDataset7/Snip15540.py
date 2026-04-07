def setUp(self):
        self.holder_change_url = reverse(
            "admin:admin_inlines_holder2_change", args=(self.holder.id,)
        )
        self.client.force_login(self.user)