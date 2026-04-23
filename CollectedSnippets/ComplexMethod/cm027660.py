def _freeze(self) -> None:
        self._freeze_sets()

        if self.rate_limit is None:
            if self.all_states or self.exception:
                self.rate_limit = ALL_STATES_RATE_LIMIT
            elif self.domains or self.domains_lifecycle:
                self.rate_limit = DOMAIN_STATES_RATE_LIMIT

        if self.exception:
            return

        if not self.all_states_lifecycle:
            if self.domains_lifecycle:
                self.filter_lifecycle = self._filter_lifecycle_domains
            else:
                self.filter_lifecycle = _false

        if self.all_states:
            return

        if self.domains:
            self.filter = self._filter_domains_and_entities
        elif self.entities:
            self.filter = self._filter_entities
        else:
            self.filter = _false