def convert_to_record(self, value, record):
        # cache format -> record format (list of dicts)
        if not value:
            return []

        # return a copy of the definition in cache where all property
        # definitions have been cleaned up
        result = []

        for property_definition in value:
            if not all(property_definition.get(key) for key in self.REQUIRED_KEYS):
                # some required keys are missing, ignore this property definition
                continue

            # don't modify the value in cache
            property_definition = copy.deepcopy(property_definition)

            type_ = property_definition.get('type')

            if type_ in ('many2one', 'many2many'):
                # check if the model still exists in the environment, the module of the
                # model might have been uninstalled so the model might not exist anymore
                property_model = property_definition.get('comodel')
                if property_model not in record.env:
                    property_definition['comodel'] = False
                    property_definition.pop('domain', None)
                elif property_domain := property_definition.get('domain'):
                    # some fields in the domain might have been removed
                    # (e.g. if the module has been uninstalled)
                    # check if the domain is still valid
                    try:
                        dom = Domain(ast.literal_eval(property_domain))
                        model = record.env[property_model]
                        dom.validate(model)
                    except ValueError:
                        del property_definition['domain']

            elif type_ in ('selection', 'tags'):
                # always set at least an empty array if there's no option
                property_definition[type_] = property_definition.get(type_) or []

            result.append(property_definition)

        return result