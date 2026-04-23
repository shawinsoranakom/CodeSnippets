def _get_entity_name_tuples(
        self, exposed: bool
    ) -> Iterable[tuple[str, str, dict[str, Any]]]:
        """Yield (input name, output name, context) tuples for entities."""
        entity_registry = er.async_get(self.hass)

        for state in self.hass.states.async_all():
            entity_exposed = async_should_expose(self.hass, DOMAIN, state.entity_id)
            if exposed and (not entity_exposed):
                # Required exposed, entity is not
                continue

            if (not exposed) and entity_exposed:
                # Required not exposed, entity is
                continue

            # Checked against "requires_context" and "excludes_context" in hassil
            context = {"domain": state.domain}
            if state.attributes:
                # Include some attributes
                for attr in _DEFAULT_EXPOSED_ATTRIBUTES:
                    if attr not in state.attributes:
                        continue
                    context[attr] = state.attributes[attr]

            entity_entry = entity_registry.async_get(state.entity_id)
            for name in intent.async_get_entity_aliases(
                self.hass, entity_entry, state=state
            ):
                yield (name, name, context)