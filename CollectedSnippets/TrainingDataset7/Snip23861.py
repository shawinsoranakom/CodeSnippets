def get_success_url(self):
        return reverse("author_detail", args=[self.object.id])