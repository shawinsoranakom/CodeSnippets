def get_absolute_url(self):
        return reverse("artist_detail", kwargs={"pk": self.id})