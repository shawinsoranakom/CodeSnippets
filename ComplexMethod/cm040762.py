def update_state(target, self, reason, reason_data, state_value):
    if reason_data is None:
        reason_data = ""
    if self.state_reason == MOTO_INITIAL_UNCHECKED_REASON:
        old_state = StateValue.INSUFFICIENT_DATA
    else:
        old_state = self.state_value

    old_state_reason = self.state_reason
    old_state_update_timestamp = self.state_updated_timestamp
    target(self, reason, reason_data, state_value)

    # check the state and trigger required actions
    if not self.actions_enabled or old_state == self.state_value:
        return
    if self.state_value == "OK":
        actions = self.ok_actions
    elif self.state_value == "ALARM":
        actions = self.alarm_actions
    else:
        actions = self.insufficient_data_actions
    for action in actions:
        data = arns.parse_arn(action)
        if data["service"] == "sns":
            service = connect_to(region_name=data["region"], aws_access_key_id=data["account"]).sns
            subject = f"""{self.state_value}: "{self.name}" in {self.region_name}"""
            message = create_message_response_update_state_sns(self, old_state)
            service.publish(TopicArn=action, Subject=subject, Message=message)
        elif data["service"] == "lambda":
            service = connect_to(
                region_name=data["region"], aws_access_key_id=data["account"]
            ).lambda_
            message = create_message_response_update_state_lambda(
                self, old_state, old_state_reason, old_state_update_timestamp
            )
            service.invoke(FunctionName=lambda_function_name(action), Payload=message)
        else:
            # TODO: support other actions
            LOG.warning(
                "Action for service %s not implemented, action '%s' will not be triggered.",
                data["service"],
                action,
            )