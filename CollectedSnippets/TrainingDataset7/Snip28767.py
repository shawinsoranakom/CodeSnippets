def _model(self, current_model, field):
        model = field.model._meta.concrete_model
        return None if model == current_model else model