def add_parser(self, name, *, deprecated=False, **kwargs):
        # set prog from the existing prefix
        if kwargs.get('prog') is None:
            kwargs['prog'] = '%s %s' % (self._prog_prefix, name)

        # set color
        if kwargs.get('color') is None:
            kwargs['color'] = self._color

        aliases = kwargs.pop('aliases', ())

        if name in self._name_parser_map:
            raise ValueError(f'conflicting subparser: {name}')
        for alias in aliases:
            if alias in self._name_parser_map:
                raise ValueError(f'conflicting subparser alias: {alias}')

        # create a pseudo-action to hold the choice help
        if 'help' in kwargs:
            help = kwargs.pop('help')
            choice_action = self._ChoicesPseudoAction(name, aliases, help)
            self._choices_actions.append(choice_action)
        else:
            choice_action = None

        # create the parser and add it to the map
        parser = self._parser_class(**kwargs)
        if choice_action is not None:
            parser._check_help(choice_action)
        self._name_parser_map[name] = parser

        # make parser available under aliases also
        for alias in aliases:
            self._name_parser_map[alias] = parser

        if deprecated:
            self._deprecated.add(name)
            self._deprecated.update(aliases)

        return parser