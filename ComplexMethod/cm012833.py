def lookup_template_configs(
        self,
        kernel_inputs: KernelInputs,
        op_name: str,
        template_uids: list[str],
        template_hash_map: dict[str, str | None] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Unified function to look up template configurations for multiple templates.
        Override this method to customize lookup logic.

        Args:
            kernel_inputs: KernelInputs object containing input nodes and scalars
            op_name: Operation name (e.g., "mm", "addmm")
            template_uids: List of template identifiers (e.g., ["mm", "tma", "decompose_k"])
            template_hash_map: Optional mapping from template_uid to src_hash for validation

        Returns:
            {}: No lookup table in use, or no matches found for any template
            {"template_uid1": [config1, config2], ...}: Matches found, filtered configurations
        """
        lookup_table = self._get_lookup_table()
        if not lookup_table:
            log.debug("Lookup table: no table configured or CUDA unavailable")
            return {}

        # Try both key variants: device-specific first, then device-agnostic
        # If both exist, device-specific takes priority
        device_key, device_agnostic_key = self.make_lookup_key_variants(
            kernel_inputs, op_name
        )

        config_list = []

        for key_type, key in [
            ("device-specific", device_key),
            ("device-agnostic", device_agnostic_key),
        ]:
            if key is not None:
                config_list = lookup_table.get(key, [])
                if config_list:
                    log.debug(
                        "Lookup table: found %d configs using %s key '%s' for %s",
                        len(config_list),
                        key_type,
                        key,
                        op_name,
                    )
                    break
        else:
            log.debug(
                "Lookup table: no match for %s (tried keys: %s, %s) (table has %d keys)",
                op_name,
                device_key,
                device_agnostic_key,
                len(lookup_table),
            )
            return {}

        log.debug(
            "Lookup table: found %d configs for %s templates %s",
            len(config_list),
            op_name,
            template_uids,
        )
        # Group configs by template_id
        configs_by_template: dict[str, list[dict[str, Any]]] = {}
        for cfg in config_list:
            if not isinstance(cfg, dict):
                raise ValueError(
                    f"Config for {op_name} operation is not a dictionary: {cfg}"
                )
            if "template_id" not in cfg:
                raise ValueError(
                    f"Config for {op_name} operation missing required 'template_id' field: {cfg}"
                )

            template_id = cfg["template_id"]
            if template_id in template_uids:
                if template_id not in configs_by_template:
                    configs_by_template[template_id] = []
                configs_by_template[template_id].append(cfg)

        # Check template hashes and clean up template_id field
        result = {}
        for template_id, matching_configs in configs_by_template.items():
            filtered_configs = []
            for cfg in matching_configs:
                # Check template hash using helper function
                if not self._entry_is_valid(cfg, template_id, template_hash_map):
                    continue

                # Return a copy of the config, as we don't want to modify the original
                cconfig = copy.deepcopy(cfg)
                # Lastly, we have to throw out the template_id, as it's not a valid kwarg
                # and just used to identify which template the entry belongs to
                del cconfig["template_id"]
                # Similarly, the template_hash is not a valid kwarg
                cconfig.pop("template_hash", None)
                filtered_configs.append(cconfig)

            if filtered_configs:
                result[template_id] = filtered_configs

        return result