def save(self, commit=True):
                # change the name to "Brooklyn Bridge" just to be a jerk.
                poem = super().save(commit=False)
                poem.name = "Brooklyn Bridge"
                if commit:
                    poem.save()
                return poem