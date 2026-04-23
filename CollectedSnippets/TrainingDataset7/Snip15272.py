def check(self, **kwargs):
                errors = super().check(**kwargs)
                if not self.admin_site.is_registered(Author):
                    errors.append("AuthorAdmin missing!")
                return errors