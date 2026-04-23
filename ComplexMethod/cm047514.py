def check_signaling(self, cr: BaseCursor | None = None) -> Registry:
        """ Check whether the registry has changed, and performs all necessary
        operations to update the registry. Return an up-to-date registry.
        """
        with nullcontext(cr) if cr is not None else closing(self.cursor(readonly=True)) as cr:
            assert cr is not None
            db_registry_sequence, db_cache_sequences = self.get_sequences(cr)
            changes = ''
            # Check if the model registry must be reloaded
            if self.registry_sequence != db_registry_sequence:
                _logger.info("Reloading the model registry after database signaling.")
                self = Registry.new(self.db_name)
                self.registry_sequence = db_registry_sequence
                if _logger.isEnabledFor(logging.DEBUG):
                    changes += "[Registry - %s -> %s]" % (self.registry_sequence, db_registry_sequence)
            # Check if the model caches must be invalidated.
            else:
                invalidated = []
                for cache_name, cache_sequence in self.cache_sequences.items():
                    expected_sequence = db_cache_sequences[cache_name]
                    if cache_sequence != expected_sequence:
                        for cache in _CACHES_BY_KEY[cache_name]: # don't call clear_cache to avoid signal loop
                            if cache not in invalidated:
                                invalidated.append(cache)
                                self.__caches[cache].clear()
                        self.cache_sequences[cache_name] = expected_sequence
                        if _logger.isEnabledFor(logging.DEBUG):
                            changes += "[Cache %s - %s -> %s]" % (cache_name, cache_sequence, expected_sequence)
                if invalidated:
                    _logger.info("Invalidating caches after database signaling: %s", sorted(invalidated))
            if changes:
                _logger.debug("Multiprocess signaling check: %s", changes)
        return self