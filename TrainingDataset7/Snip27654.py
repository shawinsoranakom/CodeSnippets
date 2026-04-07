def get_model_a(state):
            return [
                mod for mod in state.apps.get_models() if mod._meta.model_name == "a"
            ][0]