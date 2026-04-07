def confirm_login_allowed(self, user):
                if user.username == "inactive":
                    raise ValidationError("This user is disallowed.")
                raise ValidationError("Sorry, nobody's allowed in.")