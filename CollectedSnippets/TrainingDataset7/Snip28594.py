def save(self, commit=True):
                # change the name to "Vladimir Mayakovsky" just to be a jerk.
                author = super().save(commit=False)
                author.name = "Vladimir Mayakovsky"
                if commit:
                    author.save()
                return author