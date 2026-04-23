def add_dependency(self, model, dependency, reverse_dependency=False):
        if reverse_dependency:
            model, dependency = dependency, model
        self.dependencies[model._meta.concrete_model].add(
            dependency._meta.concrete_model
        )
        self.data.setdefault(dependency, self.data.default_factory())