def set_password_and_save(self, user, commit=True, **kwargs):
        if self.cleaned_data["set_usable_password"]:
            user = super().set_password_and_save(user, **kwargs, commit=commit)
        else:
            user.set_unusable_password()
            if commit:
                user.save()
        return user