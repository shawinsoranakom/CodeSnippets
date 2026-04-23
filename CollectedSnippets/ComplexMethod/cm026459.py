def find_matches(
        automations: list[BaseAutomationEntity],
        automation_configs: list[AutomationEntityConfig],
    ) -> tuple[set[int], set[int]]:
        """Find matches between a list of automation entities and a list of configurations.

        An automation or configuration is only allowed to match at most once to handle
        the case of multiple automations with identical configuration.

        Returns a tuple of sets of indices: ({automation_matches}, {config_matches})
        """
        automation_matches: set[int] = set()
        config_matches: set[int] = set()
        automation_configs_with_id: dict[str, tuple[int, AutomationEntityConfig]] = {}
        automation_configs_without_id: list[tuple[int, AutomationEntityConfig]] = []

        for config_idx, automation_config in enumerate(automation_configs):
            if automation_id := automation_config.config_block.get(CONF_ID):
                automation_configs_with_id[automation_id] = (
                    config_idx,
                    automation_config,
                )
                continue
            automation_configs_without_id.append((config_idx, automation_config))

        for automation_idx, automation in enumerate(automations):
            if automation.unique_id:
                if automation.unique_id not in automation_configs_with_id:
                    continue
                config_idx, automation_config = automation_configs_with_id.pop(
                    automation.unique_id
                )
                if automation_matches_config(automation, automation_config):
                    automation_matches.add(automation_idx)
                    config_matches.add(config_idx)
                continue

            for config_idx, automation_config in automation_configs_without_id:
                if config_idx in config_matches:
                    # Only allow an automation config to match at most once
                    continue
                if automation_matches_config(automation, automation_config):
                    automation_matches.add(automation_idx)
                    config_matches.add(config_idx)
                    # Only allow an automation to match at most once
                    break

        return automation_matches, config_matches