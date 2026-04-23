def _set_tracked(self, entity_ids: Collection[str] | None) -> None:
        """Tuple of entities to be tracked."""
        # tracking are the entities we want to track
        # trackable are the entities we actually watch

        if not entity_ids:
            self.tracking = ()
            self.trackable = ()
            self.single_state_type_key = None
            return

        registry = self._registry
        excluded_domains = registry.exclude_domains

        tracking: list[str] = []
        trackable: list[str] = []
        single_state_type_set: set[SingleStateType] = set()
        for ent_id in entity_ids:
            ent_id_lower = ent_id.lower()
            domain = split_entity_id(ent_id_lower)[0]
            tracking.append(ent_id_lower)
            if domain not in excluded_domains:
                trackable.append(ent_id_lower)
            if domain in registry.state_group_mapping:
                single_state_type_set.add(registry.state_group_mapping[domain])
            elif domain == DOMAIN:
                # If a group contains another group we check if that group
                # has a specific single state type
                if ent_id in registry.state_group_mapping:
                    single_state_type_set.add(registry.state_group_mapping[ent_id])
            else:
                single_state_type_set.add(SingleStateType(STATE_ON, STATE_OFF))

        if len(single_state_type_set) == 1:
            self.single_state_type_key = next(iter(single_state_type_set))
            # To support groups with nested groups we store the state type
            # per group entity_id if there is a single state type
            registry.state_group_mapping[self.entity_id] = self.single_state_type_key
        else:
            self.single_state_type_key = None

        self.trackable = tuple(trackable)
        self.tracking = tuple(tracking)