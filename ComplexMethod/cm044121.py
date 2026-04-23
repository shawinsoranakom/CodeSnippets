def validate_config_consistency(self) -> "MCPConfigModel":
        """Validate overall configuration consistency."""
        # If expose is False, other configurations don't matter much, but we still validate them
        if self.expose is False:
            # Could add warnings here if other fields are set when expose=False
            pass

        # Validate prompt names are unique within this config
        if self.prompts:
            prompt_names = []
            for prompt in self.prompts:
                if prompt.name:
                    prompt_names.append(prompt.name)

            # Check for duplicate names
            if len(prompt_names) != len(set(prompt_names)):
                duplicates = [
                    name for name in prompt_names if prompt_names.count(name) > 1
                ]
                raise ValueError(f"Duplicate prompt names found: {set(duplicates)}")

        return self