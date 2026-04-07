def apply_next_model(model):
                next_function = partial(apply_next_model.func, model)
                self.lazy_model_operation(next_function, *more_models)