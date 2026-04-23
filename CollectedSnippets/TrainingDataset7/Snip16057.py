def get_urls(self):
        return [
            path("my_view/", self.admin_view(self.my_view), name="my_view"),
        ] + super().get_urls()