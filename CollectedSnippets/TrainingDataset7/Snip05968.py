def base_url_parameters(self):
        limit_choices_to = self.rel.limit_choices_to
        if callable(limit_choices_to):
            limit_choices_to = limit_choices_to()
        return url_params_from_lookup_dict(limit_choices_to)