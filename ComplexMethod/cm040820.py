def delete_state_machine_version(
        self, context: RequestContext, state_machine_version_arn: LongArn, **kwargs
    ) -> DeleteStateMachineVersionOutput:
        self._validate_state_machine_arn(state_machine_version_arn)
        state_machines = self.get_store(context).state_machines

        if not (
            state_machine_version := state_machines.get(state_machine_version_arn)
        ) or not isinstance(state_machine_version, StateMachineVersion):
            return DeleteStateMachineVersionOutput()

        if (
            state_machine_revision := state_machines.get(state_machine_version.source_arn)
        ) and isinstance(state_machine_revision, StateMachineRevision):
            referencing_alias_names: list[str] = []
            for alias in state_machine_revision.aliases:
                if alias.is_router_for(state_machine_version_arn=state_machine_version_arn):
                    referencing_alias_names.append(alias.name)
            if referencing_alias_names:
                referencing_alias_names_list_body = ", ".join(referencing_alias_names)
                raise ConflictException(
                    "Version to be deleted must not be referenced by an alias. "
                    f"Current list of aliases referencing this version: [{referencing_alias_names_list_body}]"
                )
            state_machine_revision.delete_version(state_machine_version_arn)

        state_machines.pop(state_machine_version.arn, None)
        return DeleteStateMachineVersionOutput()