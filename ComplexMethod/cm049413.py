def _get_unique_names(self, model_name, names):
        """Generate unique names for the given model.

        Take a list of names and return for each names, the new names to set
        in the same order (with a counter added if needed).

        E.G.
            The name "test" already exists in database
            Input: ['test', 'test [3]', 'bob', 'test', 'test']
            Output: ['test [2]', 'test [3]', 'bob', 'test [4]', 'test [5]']

        :param model_name: name of the model for which we will generate unique names
        :param names: list of names, we will ensure that each name will be unique
        :return: a list of new values for each name, in the same order
        """
        # Avoid conflicting with itself, otherwise each check at update automatically
        # increments counters
        skip_record_ids = self.env.context.get("utm_check_skip_record_ids") or []
        # Remove potential counter part in each names
        names_without_counter = {self._split_name_and_count(name)[0] for name in names}

        # Retrieve existing similar names
        search_domain = Domain.OR(Domain('name', 'ilike', name) for name in names_without_counter)
        if skip_record_ids:
            search_domain &= Domain('id', 'not in', skip_record_ids)
        existing_names = {vals['name'] for vals in self.env[model_name].search_read(search_domain, ['name'])}

        # Counter for each names, based on the names list given in argument
        # and the record names in database
        used_counters_per_name = {
            name: {
                self._split_name_and_count(existing_name)[1]
                for existing_name in existing_names
                if existing_name == name or existing_name.startswith(f'{name} [')
            } for name in names_without_counter
        }
        # Automatically incrementing counters for each name, will be used
        # to fill holes in used_counters_per_name
        current_counter_per_name = defaultdict(lambda: itertools.count(1))

        result = []
        for name in names:
            if not name:
                result.append(False)
                continue

            name_without_counter, asked_counter = self._split_name_and_count(name)
            existing = used_counters_per_name.get(name_without_counter, set())
            if asked_counter and asked_counter not in existing:
                count = asked_counter
            else:
                # keep going until the count is not already used
                for count in current_counter_per_name[name_without_counter]:
                    if count not in existing:
                        break
            existing.add(count)
            result.append(f'{name_without_counter} [{count}]' if count > 1 else name_without_counter)

        return result