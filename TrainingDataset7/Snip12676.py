def choice(self, obj):
        return (
            ModelChoiceIteratorValue(self.field.prepare_value(obj), obj),
            self.field.label_from_instance(obj),
        )