def if_in_zone(**kwargs: Unpack[ConditionCheckParams]) -> bool:
            """Test if condition."""
            errors = []

            all_ok = True
            for entity_id in entity_ids:
                entity_ok = False
                for zone_entity_id in zone_entity_ids:
                    try:
                        if zone(self._hass, zone_entity_id, entity_id):
                            entity_ok = True
                    except ConditionErrorMessage as ex:
                        errors.append(
                            ConditionErrorMessage(
                                "zone",
                                (
                                    f"error matching {entity_id} with {zone_entity_id}:"
                                    f" {ex.message}"
                                ),
                            )
                        )

                if not entity_ok:
                    all_ok = False

            # Raise the errors only if no definitive result was found
            if errors and not all_ok:
                raise ConditionErrorContainer("zone", errors=errors)

            return all_ok