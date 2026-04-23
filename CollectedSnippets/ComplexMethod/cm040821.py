def update_state_machine(
        self,
        context: RequestContext,
        state_machine_arn: Arn,
        definition: Definition = None,
        role_arn: Arn = None,
        logging_configuration: LoggingConfiguration = None,
        tracing_configuration: TracingConfiguration = None,
        publish: Publish = None,
        version_description: VersionDescription = None,
        encryption_configuration: EncryptionConfiguration = None,
        **kwargs,
    ) -> UpdateStateMachineOutput:
        self._validate_state_machine_arn(state_machine_arn)
        state_machines = self.get_store(context).state_machines

        state_machine = state_machines.get(state_machine_arn)
        if not isinstance(state_machine, StateMachineRevision):
            self._raise_state_machine_does_not_exist(state_machine_arn)

        # TODO: Add logic to handle metrics for when SFN definitions update
        if not any([definition, role_arn, logging_configuration]):
            raise MissingRequiredParameter(
                "Either the definition, the role ARN, the LoggingConfiguration, "
                "or the TracingConfiguration must be specified"
            )

        if definition is not None:
            self._validate_definition(definition=definition, static_analysers=[StaticAnalyser()])

        if logging_configuration is not None:
            self._sanitise_logging_configuration(logging_configuration=logging_configuration)

        revision_id = state_machine.create_revision(
            definition=definition,
            role_arn=role_arn,
            logging_configuration=logging_configuration,
        )

        version_arn = None
        if publish:
            version = state_machine.create_version(description=version_description)
            if version is not None:
                version_arn = version.arn
                state_machines[version_arn] = version
            else:
                target_revision_id = revision_id or state_machine.revision_id
                version_arn = state_machine.versions[target_revision_id]

        update_output = UpdateStateMachineOutput(updateDate=datetime.datetime.now(tz=datetime.UTC))
        if revision_id is not None:
            update_output["revisionId"] = revision_id
        if version_arn is not None:
            update_output["stateMachineVersionArn"] = version_arn
        return update_output