def filter(self, targets: tuple[IntegrationTarget, ...], exclude: list[str]) -> None:
        """Filter out the cloud tests when the necessary config and resources are not available."""
        if not self.uses_docker and not self.uses_config:
            return

        if self.uses_docker and docker_available():
            return

        if self.uses_config and os.path.exists(self.config_static_path):
            return

        skip = 'cloud/%s/' % self.platform
        skipped = [target.name for target in targets if skip in target.aliases]

        if skipped:
            exclude.append(skip)

            if not self.uses_docker and self.uses_config:
                display.warning('Excluding tests marked "%s" which require a "%s" config file (see "%s"): %s'
                                % (skip.rstrip('/'), self.config_static_path, self.config_template_path, ', '.join(skipped)))
            elif self.uses_docker and not self.uses_config:
                display.warning('Excluding tests marked "%s" which requires container support: %s'
                                % (skip.rstrip('/'), ', '.join(skipped)))
            elif self.uses_docker and self.uses_config:
                display.warning('Excluding tests marked "%s" which requires container support or a "%s" config file (see "%s"): %s'
                                % (skip.rstrip('/'), self.config_static_path, self.config_template_path, ', '.join(skipped)))