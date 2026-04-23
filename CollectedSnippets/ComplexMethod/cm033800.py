def _validate_semantic_markup(self, object) -> None:
        # Make sure we operate on strings
        if is_iterable(object):
            for entry in object:
                self._validate_semantic_markup(entry)
            return
        if not isinstance(object, str):
            return

        if self.collection:
            fqcn = f'{self.collection_name}.{self.name}'
        else:
            fqcn = f'ansible.builtin.{self.name}'
        current_plugin = dom.PluginIdentifier(fqcn=fqcn, type=self.plugin_type)
        for par in parse(object, Context(current_plugin=current_plugin), errors='message', add_source=True):
            for part in par:
                # Errors are already covered during schema validation, we only check for option and
                # return value references
                if part.type == dom.PartType.OPTION_NAME:
                    self._check_sem_option(part, current_plugin)
                if part.type == dom.PartType.RETURN_VALUE:
                    self._check_sem_return_value(part, current_plugin)