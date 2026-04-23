def unique_ids(self) -> set[tuple[Platform, str]]:
        """Return all the unique ids for a config entry id."""
        current_unique_ids: set[tuple[Platform, str]] = {
            (Platform.BUTTON, f"{self.uuid}_query")
        }

        # Structure and prefixes here must match what's added in __init__ and helpers
        for platform in NODE_PLATFORMS:
            for node in self.nodes[platform]:
                current_unique_ids.add((platform, self.uid_base(node)))

        for platform in NODE_AUX_PROP_PLATFORMS:
            for node, control in self.aux_properties[platform]:
                current_unique_ids.add((platform, f"{self.uid_base(node)}_{control}"))

        for platform in PROGRAM_PLATFORMS:
            for _, node, _ in self.programs[platform]:
                current_unique_ids.add((platform, self.uid_base(node)))

        for platform in VARIABLE_PLATFORMS:
            for node in self.variables[platform]:
                current_unique_ids.add((platform, self.uid_base(node)))
                if platform == Platform.NUMBER:
                    current_unique_ids.add((platform, f"{self.uid_base(node)}_init"))

        for platform in ROOT_NODE_PLATFORMS:
            for node in self.root_nodes[platform]:
                current_unique_ids.add((platform, f"{self.uid_base(node)}_query"))
                if platform == Platform.BUTTON and node.protocol == PROTO_INSTEON:
                    current_unique_ids.add((platform, f"{self.uid_base(node)}_beep"))

        for node in self.net_resources:
            current_unique_ids.add((Platform.BUTTON, self.uid_base(node)))

        return current_unique_ids