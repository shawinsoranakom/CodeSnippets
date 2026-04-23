def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)