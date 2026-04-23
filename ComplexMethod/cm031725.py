def _render_non_self(
            self,
            parameter: Parameter,
            data: CRenderData
    ) -> None:
        self.parameter = parameter
        name = self.name

        # declarations
        d = self.declaration(in_parser=True)
        data.declarations.append(d)

        # initializers
        initializers = self.initialize()
        if initializers:
            data.initializers.append('/* initializers for ' + name + ' */\n' + initializers.rstrip())

        # modifications
        modifications = self.modify()
        if modifications:
            data.modifications.append('/* modifications for ' + name + ' */\n' + modifications.rstrip())

        # keywords
        if parameter.is_variable_length():
            pass
        elif parameter.is_positional_only():
            data.keywords.append('')
        else:
            data.keywords.append(parameter.name)

        # format_units
        if self.is_optional() and '|' not in data.format_units:
            data.format_units.append('|')
        if parameter.is_keyword_only() and '$' not in data.format_units:
            data.format_units.append('$')
        data.format_units.append(self.format_unit)

        # parse_arguments
        self.parse_argument(data.parse_arguments)

        # post_parsing
        if post_parsing := self.post_parsing():
            data.post_parsing.append('/* Post parse cleanup for ' + name + ' */\n' + post_parsing.rstrip() + '\n')

        # cleanup
        cleanup = self.cleanup()
        if cleanup:
            data.cleanup.append('/* Cleanup for ' + name + ' */\n' + cleanup.rstrip() + "\n")