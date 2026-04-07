def get_absolute_url(self):
        return reverse("i18n_testmodel", args=[self.id])