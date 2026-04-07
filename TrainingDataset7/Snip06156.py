def set_password_and_save(self, user, password_field_name="password1", commit=True):
        user.set_password(self.cleaned_data[password_field_name])
        if commit:
            user.save()
        return user