def _search_panel_field_image(self, field_name, **kwargs):
        """
        Return the values in the image of the provided domain by field_name.

        :param field_name: the name of a field (type ``many2one`` or
            ``selection``)
        :param kwargs: Keyword arguments:

            * ``model_domain``: domain whose image is returned
            * ``extra_domain``: extra domain to use when counting records
              associated with field values
            * ``enable_counters``: whether to set the key ``'__count'`` in
              image values
            * ``only_counters``: whether to retrieve information on the
              ``model_domain`` image or only counts based on
              ``model_domain`` and ``extra_domain``. In the later case,
              the counts are set whatever is enable_counters.
            * ``limit``: maximal number of values to fetch
            * ``set_limit``: whether to use the provided limit (if any)
        :return: a dict of the form:
            ::

                {
                    id: { 'id': id, 'display_name': display_name, ('__count': c,) },
                    ...
                }
        """

        enable_counters = kwargs.get('enable_counters')
        only_counters = kwargs.get('only_counters')
        extra_domain = Domain(kwargs.get('extra_domain', []))
        no_extra = extra_domain.is_true()
        model_domain = Domain(kwargs.get('model_domain', []))
        count_domain = model_domain & extra_domain

        limit = kwargs.get('limit')
        set_limit = kwargs.get('set_limit')

        if only_counters:
            return self._search_panel_domain_image(field_name, count_domain, True)

        model_domain_image = self._search_panel_domain_image(field_name, model_domain,
                            enable_counters and no_extra,
                            set_limit and limit,
                        )
        if enable_counters and not no_extra:
            count_domain_image = self._search_panel_domain_image(field_name, count_domain, True)
            for id, values in model_domain_image.items():
                element = count_domain_image.get(id)
                values['__count'] = element['__count'] if element else 0

        return model_domain_image