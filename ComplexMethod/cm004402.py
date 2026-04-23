def _check_entity_input_format(self, entities: EntityInput | None, entity_spans: EntitySpanInput | None):
        if not isinstance(entity_spans, list):
            raise TypeError("entity_spans should be given as a list")
        elif len(entity_spans) > 0 and not isinstance(entity_spans[0], tuple):
            raise ValueError(
                "entity_spans should be given as a list of tuples containing the start and end character indices"
            )

        if entities is not None:
            if not isinstance(entities, list):
                raise ValueError("If you specify entities, they should be given as a list")

            if len(entities) > 0 and not isinstance(entities[0], str):
                raise ValueError("If you specify entities, they should be given as a list of entity names")

            if len(entities) != len(entity_spans):
                raise ValueError("If you specify entities, entities and entity_spans must be the same length")