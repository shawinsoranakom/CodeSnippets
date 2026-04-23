def rule_is_enumerable(self, rule):
        """ Checks that it is possible to generate sensible GET queries for
            a given rule (if the endpoint matches its own requirements)
            :type rule: werkzeug.routing.Rule
            :rtype: bool
        """
        endpoint = rule.endpoint
        methods = endpoint.routing.get('methods') or ['GET']

        converters = list(rule._converters.values())
        if not ('GET' in methods
                and endpoint.routing['type'] == 'http'
                and endpoint.routing['auth'] in ('none', 'public')
                and endpoint.routing.get('website', False)
                and all(hasattr(converter, 'generate') for converter in converters)):
            return False

        # dont't list routes without argument having no default value or converter
        sign = inspect.signature(endpoint.original_endpoint)
        params = list(sign.parameters.values())[1:]  # skip self
        supported_kinds = (inspect.Parameter.POSITIONAL_ONLY,
                           inspect.Parameter.POSITIONAL_OR_KEYWORD)

        # check that all args have a converter
        return all(p.name in rule._converters for p in params
                   if p.kind in supported_kinds and p.default is inspect.Parameter.empty)