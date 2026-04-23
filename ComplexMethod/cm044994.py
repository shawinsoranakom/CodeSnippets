def _evaluate_condition(self, condition: str, extension_id: Optional[str]) -> bool:
        """Evaluate a hook condition expression.

        Supported condition patterns:
        - "config.key.path is set" - checks if config value exists
        - "config.key.path == 'value'" - checks if config equals value
        - "config.key.path != 'value'" - checks if config not equals value
        - "env.VAR_NAME is set" - checks if environment variable exists
        - "env.VAR_NAME == 'value'" - checks if env var equals value

        Args:
            condition: Condition expression string
            extension_id: Extension ID for config lookup

        Returns:
            True if condition is met, False otherwise
        """
        import os

        condition = condition.strip()

        # Pattern: "config.key.path is set"
        if match := re.match(r'config\.([a-z0-9_.]+)\s+is\s+set', condition, re.IGNORECASE):
            key_path = match.group(1)
            if not extension_id:
                return False

            config_manager = ConfigManager(self.project_root, extension_id)
            return config_manager.has_value(key_path)

        # Pattern: "config.key.path == 'value'" or "config.key.path != 'value'"
        if match := re.match(r'config\.([a-z0-9_.]+)\s*(==|!=)\s*["\']([^"\']+)["\']', condition, re.IGNORECASE):
            key_path = match.group(1)
            operator = match.group(2)
            expected_value = match.group(3)

            if not extension_id:
                return False

            config_manager = ConfigManager(self.project_root, extension_id)
            actual_value = config_manager.get_value(key_path)

            # Normalize boolean values to lowercase for comparison
            # (YAML True/False vs condition strings 'true'/'false')
            if isinstance(actual_value, bool):
                normalized_value = "true" if actual_value else "false"
            else:
                normalized_value = str(actual_value)

            if operator == "==":
                return normalized_value == expected_value
            else:  # !=
                return normalized_value != expected_value

        # Pattern: "env.VAR_NAME is set"
        if match := re.match(r'env\.([A-Z0-9_]+)\s+is\s+set', condition, re.IGNORECASE):
            var_name = match.group(1).upper()
            return var_name in os.environ

        # Pattern: "env.VAR_NAME == 'value'" or "env.VAR_NAME != 'value'"
        if match := re.match(r'env\.([A-Z0-9_]+)\s*(==|!=)\s*["\']([^"\']+)["\']', condition, re.IGNORECASE):
            var_name = match.group(1).upper()
            operator = match.group(2)
            expected_value = match.group(3)

            actual_value = os.environ.get(var_name, "")

            if operator == "==":
                return actual_value == expected_value
            else:  # !=
                return actual_value != expected_value

        # Unknown condition format, default to False for safety
        return False