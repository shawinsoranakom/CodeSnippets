def _get_number_value(self, values):
                try:
                    return values[number]
                except KeyError:
                    raise KeyError(
                        "Your dictionary lacks key '%s'. Please provide "
                        "it, because it is required to determine whether "
                        "string is singular or plural." % number
                    )