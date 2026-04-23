def _validate_state_machine_alias_routing_configuration(
        self, context: RequestContext, routing_configuration_list: RoutingConfigurationList
    ) -> None:
        # TODO: to match AWS's approach best validation exceptions could be
        #  built in a process decoupled from the provider.

        routing_configuration_list_len = len(routing_configuration_list)
        if not (1 <= routing_configuration_list_len <= 2):
            # Replicate the object string dump format:
            # [RoutingConfigurationListItem(stateMachineVersionArn=arn_no_quotes, weight=int), ...]
            routing_configuration_serialization_parts = []
            for routing_configuration in routing_configuration_list:
                routing_configuration_serialization_parts.append(
                    "".join(
                        [
                            "RoutingConfigurationListItem(stateMachineVersionArn=",
                            routing_configuration["stateMachineVersionArn"],
                            ", weight=",
                            str(routing_configuration["weight"]),
                            ")",
                        ]
                    )
                )
            routing_configuration_serialization_list = (
                f"[{', '.join(routing_configuration_serialization_parts)}]"
            )
            raise ValidationException(
                f"1 validation error detected: Value '{routing_configuration_serialization_list}' "
                "at 'routingConfiguration' failed to "
                "satisfy constraint: Member must have length less than or equal to 2"
            )

        routing_configuration_arn_list = [
            routing_configuration["stateMachineVersionArn"]
            for routing_configuration in routing_configuration_list
        ]
        if len(set(routing_configuration_arn_list)) < routing_configuration_list_len:
            arn_list_string = f"[{', '.join(routing_configuration_arn_list)}]"
            raise ValidationException(
                "Routing configuration must contain distinct state machine version ARNs. "
                f"Received: {arn_list_string}"
            )

        routing_weights = [
            routing_configuration["weight"] for routing_configuration in routing_configuration_list
        ]
        for i, weight in enumerate(routing_weights):
            # TODO: check for weight type.
            if weight < 0:
                raise ValidationException(
                    f"Invalid value for parameter routingConfiguration[{i + 1}].weight, value: {weight}, valid min value: 0"
                )
            if weight > 100:
                raise ValidationException(
                    f"1 validation error detected: Value '{weight}' at 'routingConfiguration.{i + 1}.member.weight' "
                    "failed to satisfy constraint: Member must have value less than or equal to 100"
                )
        routing_weights_sum = sum(routing_weights)
        if not routing_weights_sum == 100:
            raise ValidationException(
                f"Sum of routing configuration weights must equal 100. Received: {json.dumps(routing_weights)}"
            )

        store = self.get_store(context=context)
        state_machines = store.state_machines

        first_routing_qualified_arn = routing_configuration_arn_list[0]
        shared_state_machine_revision_arn = self._get_state_machine_arn_from_qualified_arn(
            qualified_arn=first_routing_qualified_arn
        )
        for routing_configuration_arn in routing_configuration_arn_list:
            maybe_state_machine_version = state_machines.get(routing_configuration_arn)
            if not isinstance(maybe_state_machine_version, StateMachineVersion):
                arn_list_string = f"[{', '.join(routing_configuration_arn_list)}]"
                raise ValidationException(
                    f"Routing configuration must contain state machine version ARNs. Received: {arn_list_string}"
                )
            state_machine_revision_arn = self._get_state_machine_arn_from_qualified_arn(
                qualified_arn=routing_configuration_arn
            )
            if state_machine_revision_arn != shared_state_machine_revision_arn:
                raise ValidationException("TODO")