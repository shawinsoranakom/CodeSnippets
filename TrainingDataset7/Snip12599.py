def cleaned_data(self):
        """
        Return a list of form.cleaned_data dicts for every form in self.forms.
        """
        if not self.is_valid():
            raise AttributeError(
                "'%s' object has no attribute 'cleaned_data'" % self.__class__.__name__
            )
        return [form.cleaned_data for form in self.forms]