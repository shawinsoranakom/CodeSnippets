async def _async_add_entity(  # noqa: C901
        self,
        entity: Entity,
        update_before_add: bool,
        entity_registry: EntityRegistry,
        config_subentry_id: str | None,
    ) -> None:
        """Add an entity to the platform."""
        if entity is None:
            raise ValueError("Entity cannot be None")

        entity.add_to_platform_start(
            self.hass,
            self,
            self._get_parallel_updates_semaphore(hasattr(entity, "update")),
        )

        # Update properties before we generate the entity_id. This will happen
        # also for disabled entities.
        if update_before_add:
            try:
                await entity.async_device_update(warning=False)
            except Exception:
                self.logger.exception("%s: Error on device update!", self.platform_name)
                entity.add_to_platform_abort()
                return

        entity_name = entity.name
        if entity_name is UNDEFINED:
            entity_name = None

        suggested_object_id: str | None = None

        # An entity may suggest the entity_id by setting entity_id itself
        if not hasattr(entity, "internal_integration_suggested_object_id"):
            if entity.entity_id is None:
                entity.internal_integration_suggested_object_id = None  # type: ignore[unreachable]
            else:
                if not valid_entity_id(entity.entity_id):
                    if entity.unique_id is not None:
                        report_usage(
                            f"sets an invalid entity ID: '{entity.entity_id}'. "
                            "In most cases, entities should not set entity_id,"
                            " but if they do, it should be a valid entity ID",
                            integration_domain=self.platform_name,
                            breaks_in_ha_version="2027.2.0",
                        )
                    else:
                        entity.add_to_platform_abort()
                        raise HomeAssistantError(
                            f"Invalid entity ID: {entity.entity_id}"
                        )
                try:
                    domain, entity.internal_integration_suggested_object_id = (
                        split_entity_id(entity.entity_id)
                    )
                    if domain != self.domain:
                        report_usage(
                            f"sets an entity ID with wrong domain: '{entity.entity_id}'. "
                            f"Expected domain is '{self.domain}'",
                            integration_domain=self.platform_name,
                            breaks_in_ha_version="2027.5.0",
                        )
                except ValueError:
                    # This error handling should be removed once we remove
                    # the invalid entity ID deprecation above.
                    entity.add_to_platform_abort()
                    raise HomeAssistantError(
                        f"Invalid entity ID: {entity.entity_id}"
                    ) from None

        # Get entity_id from unique ID registration
        if entity.unique_id is not None:
            registered_entity_id = entity_registry.async_get_entity_id(
                self.domain, self.platform_name, entity.unique_id
            )
            if registered_entity_id:
                already_exists, _ = self._entity_id_already_exists(registered_entity_id)

                if already_exists:
                    # If there's a collision, the entry belongs to another entity
                    entity.registry_entry = None
                    msg = (
                        f"Platform {self.platform_name} does not generate unique IDs. "
                    )
                    if entity.entity_id:
                        msg += (
                            f"ID {entity.unique_id} is already used by"
                            f" {registered_entity_id} - ignoring {entity.entity_id}"
                        )
                    else:
                        msg += (
                            f"ID {entity.unique_id} already exists - ignoring"
                            f" {registered_entity_id}"
                        )
                    self.logger.error(msg)
                    entity.add_to_platform_abort()
                    return

            device: dr.DeviceEntry | None
            if self.config_entry:
                if device_info := entity.device_info:
                    try:
                        device = dr.async_get(self.hass).async_get_or_create(
                            config_entry_id=self.config_entry.entry_id,
                            config_subentry_id=config_subentry_id,
                            **device_info,
                        )
                    except dr.DeviceInfoError as exc:
                        self.logger.error(
                            "%s: Not adding entity with invalid device info: %s",
                            self.platform_name,
                            str(exc),
                        )
                        entity.add_to_platform_abort()
                        return

                    entity.device_entry = device
                else:
                    device = entity.device_entry
            else:
                device = None

            suggested_object_id, object_id_base = _async_derive_object_ids(entity, self)

            disabled_by: RegistryEntryDisabler | None = None
            if not entity.entity_registry_enabled_default:
                disabled_by = RegistryEntryDisabler.INTEGRATION

            hidden_by: RegistryEntryHider | None = None
            if not entity.entity_registry_visible_default:
                hidden_by = RegistryEntryHider.INTEGRATION

            entry = entity_registry.async_get_or_create(
                self.domain,
                self.platform_name,
                entity.unique_id,
                capabilities=entity.capability_attributes,
                config_entry=self.config_entry,
                config_subentry_id=config_subentry_id,
                device_id=device.id if device else None,
                disabled_by=disabled_by,
                entity_category=entity.entity_category,
                get_initial_options=entity.get_initial_entity_options,
                has_entity_name=entity.has_entity_name,
                hidden_by=hidden_by,
                object_id_base=object_id_base,
                original_device_class=entity.device_class,
                original_icon=entity.icon,
                original_name=entity_name,
                suggested_object_id=suggested_object_id,
                supported_features=entity.supported_features,
                translation_key=entity.translation_key,
                unit_of_measurement=entity.unit_of_measurement,
            )

            if device and device.disabled and not entry.disabled:
                entry = entity_registry.async_update_entity(
                    entry.entity_id, disabled_by=RegistryEntryDisabler.DEVICE
                )

            entity.registry_entry = entry
            entity.entity_id = entry.entity_id

        else:  # entity.unique_id is None  # noqa: PLR5501
            # We won't generate an entity ID if the platform has already set one
            # We will however make sure that platform cannot pick a registered ID
            if entity.entity_id is None or entity_registry.async_is_registered(
                entity.entity_id
            ):
                object_ids = _async_derive_object_ids(
                    entity, self, fallback_object_id=DEVICE_DEFAULT_NAME
                )
                suggested_object_id = (
                    object_ids[0] if object_ids[0] is not None else object_ids[1]
                )
                entity.entity_id = entity_registry.async_get_available_entity_id(
                    self.domain, suggested_object_id
                )

        already_exists, restored = self._entity_id_already_exists(entity.entity_id)

        if already_exists:
            self.logger.error(
                "Entity id already exists - ignoring: %s", entity.entity_id
            )
            entity.add_to_platform_abort()
            return

        if entity.registry_entry and entity.registry_entry.disabled:
            self.logger.debug(
                "Not adding entity %s because it's disabled",
                entry.name
                or entity_name
                or f'"{self.platform_name} {entity.unique_id}"',
            )
            entity.add_to_platform_abort()
            return

        entity_id = entity.entity_id
        self.entities[entity_id] = entity
        self.domain_entities[entity_id] = entity
        self.domain_platform_entities[entity_id] = entity

        if not restored:
            # Reserve the state in the state machine
            # because as soon as we return control to the event
            # loop below, another entity could be added
            # with the same id before `entity.add_to_platform_finish()`
            # has a chance to finish.
            self.hass.states.async_reserve(entity.entity_id)

        def remove_entity_cb() -> None:
            """Remove entity from entities dict."""
            del self.entities[entity_id]
            del self.domain_entities[entity_id]
            del self.domain_platform_entities[entity_id]

        entity.async_on_remove(remove_entity_cb)

        await entity.add_to_platform_finish()