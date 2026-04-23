def save_form_data(self, instance, data):
        setattr(instance, self.name, data)