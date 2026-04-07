def model_property_is_from_past(self):
        return self.date < timezone.now()