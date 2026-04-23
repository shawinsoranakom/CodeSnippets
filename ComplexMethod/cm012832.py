def _entry_is_valid(
        cfg: dict[str, Any],
        template_id: str,
        template_hash_map: dict[str, str | None] | None,
    ) -> bool:
        """
        Check if a config entry is valid based on template hash validation.

        Args:
            cfg: Configuration dictionary that may contain a template_hash field
            template_id: The template identifier
            template_hash_map: Optional mapping from template_uid to src_hash for validation

        Returns:
            True if the config is valid and should be kept, False if it should be filtered out
        """
        # If hash checking is disabled or no hash map provided, keep the config
        if not config.lookup_table.check_src_hash or not template_hash_map:
            return True

        template_hash = template_hash_map.get(template_id)
        config_hash = cfg.get("template_hash")

        # Both hashes present - validate they match
        if template_hash is not None and config_hash is not None:
            if config_hash != template_hash:
                log.warning(
                    "Hash validation failed for template '%s': config_hash='%s' != template_hash='%s'. "
                    "Template code may have changed. Filtering out config: %s",
                    template_id,
                    config_hash,
                    template_hash,
                    {k: v for k, v in cfg.items() if k != "template_hash"},
                )
                return False
            else:
                log.debug(
                    "Hash validation passed for template '%s': hash='%s'",
                    template_id,
                    template_hash,
                )
                return True
        # Config has no hash - keep it
        elif config_hash is None:
            log.debug(
                "Config for template '%s' has no hash - keeping it (template_hash='%s')",
                template_id,
                template_hash,
            )
            return True
        # Template has no hash - keep config
        else:
            log.debug(
                "Template '%s' has no src_hash - keeping config with hash '%s'",
                template_id,
                config_hash,
            )
            return True