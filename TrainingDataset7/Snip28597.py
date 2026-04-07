def save(self, commit=True):
                poem = super().save(commit=False)
                poem.name = "%s by %s" % (poem.name, poem.poet.name)
                if commit:
                    poem.save()
                return poem