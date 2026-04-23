def create_revision(
        self,
        definition: str | None,
        role_arn: Arn | None,
        logging_configuration: LoggingConfiguration | None,
    ) -> RevisionId | None:
        update_definition = definition and json.loads(definition) != json.loads(self.definition)
        if update_definition:
            self.definition = definition

        update_role_arn = role_arn and role_arn != self.role_arn
        if update_role_arn:
            self.role_arn = role_arn

        update_logging_configuration = (
            logging_configuration and logging_configuration != self.logging_config
        )
        if update_logging_configuration:
            self.logging_config = logging_configuration
            self.cloud_watch_logging_configuration = (
                CloudWatchLoggingConfiguration.from_logging_configuration(
                    state_machine_arn=self.arn, logging_configuration=self.logging_config
                )
            )

        if any([update_definition, update_role_arn, update_logging_configuration]):
            self.revision_id = long_uid()

        return self.revision_id