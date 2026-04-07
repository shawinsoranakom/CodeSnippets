def get_available_name(self, name, max_length=None):
        """
        Append numbers to duplicate files rather than underscores, like Trac.
        """
        basename, *ext = os.path.splitext(name)
        number = 2
        while self.exists(name):
            name = "".join([basename, ".", str(number)] + ext)
            number += 1

        return name