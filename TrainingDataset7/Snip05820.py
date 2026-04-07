def get_model_admin(self, model):
        try:
            return self._registry[model]
        except KeyError:
            raise NotRegistered(f"The model {model.__name__} is not registered.")