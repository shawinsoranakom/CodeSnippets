async def _make_slot_lists(self) -> dict[str, SlotList]:
        """Create slot lists with areas and entity names/aliases."""
        if self._slot_lists is not None:
            return self._slot_lists

        start = time.monotonic()

        # Gather entity names, keeping track of exposed names.
        # We try intent recognition with only exposed names first, then all names.
        #
        # NOTE: We do not pass entity ids in here because multiple entities may
        # have the same name. The intent matcher doesn't gather all matching
        # values for a list, just the first. So we will need to match by name no
        # matter what.
        exposed_entity_names = list(self._get_entity_name_tuples(exposed=True))
        _LOGGER.debug("Exposed entities: %s", exposed_entity_names)

        # Expose all areas.
        areas = ar.async_get(self.hass)
        area_names = []
        for area in areas.async_list_areas():
            area_names.append((area.name, area.name))
            if not area.aliases:
                continue

            for alias in area.aliases:
                alias = alias.strip()
                if not alias:
                    continue

                area_names.append((alias, alias))

        # Expose all floors.
        floors = fr.async_get(self.hass)
        floor_names = []
        for floor in floors.async_list_floors():
            floor_names.append((floor.name, floor.name))
            if not floor.aliases:
                continue

            for alias in floor.aliases:
                alias = alias.strip()
                if not alias:
                    continue

                floor_names.append((alias, floor.name))

        # Build trie
        self._exposed_names_trie = Trie()
        name_list = TextSlotList.from_tuples(exposed_entity_names, allow_template=False)
        for name_value in name_list.values:
            assert isinstance(name_value.text_in, TextChunk)
            name_text = remove_punctuation(name_value.text_in.text).strip().lower()
            self._exposed_names_trie.insert(name_text, name_value)

        self._slot_lists = {
            "area": TextSlotList.from_tuples(area_names, allow_template=False),
            "name": name_list,
            "floor": TextSlotList.from_tuples(floor_names, allow_template=False),
        }

        # Reload fuzzy matchers with new slot lists
        if self.fuzzy_matching:
            await self.hass.async_add_executor_job(self._load_fuzzy_matchers)

        self._listen_clear_slot_list()

        _LOGGER.debug(
            "Created slot lists in %.2f seconds",
            time.monotonic() - start,
        )

        return self._slot_lists