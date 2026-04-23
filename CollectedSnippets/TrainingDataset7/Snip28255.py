def save_form_data(self, instance, data):
        been_here = getattr(self, "been_saved", False)
        assert not been_here, "save_form_data called more than once"
        setattr(self, "been_saved", True)