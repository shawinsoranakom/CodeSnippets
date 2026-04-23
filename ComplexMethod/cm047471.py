def _selection_modules(self, model):
        """ Return a mapping from selection values to modules defining each value. """
        if not isinstance(self.selection, list):
            return {}
        value_modules = defaultdict(set)
        for field in reversed(resolve_mro(model, self.name, type(self).__instancecheck__)):
            module = field._module
            if not module:
                continue
            if 'selection' in field._args__:
                value_modules.clear()
                if isinstance(field._args__['selection'], list):
                    for value, _label in field._args__['selection']:
                        value_modules[value].add(module)
            if 'selection_add' in field._args__:
                for value_label in field._args__['selection_add']:
                    if len(value_label) > 1:
                        value_modules[value_label[0]].add(module)
        return value_modules