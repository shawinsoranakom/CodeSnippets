def related_model(self):
        if not self.field.model:
            raise AttributeError(
                "This property can't be accessed before self.field.contribute_to_class "
                "has been called."
            )
        return self.field.model