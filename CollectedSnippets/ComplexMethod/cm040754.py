def set_alarm_state(
        self,
        context: RequestContext,
        alarm_name: AlarmName,
        state_value: StateValue,
        state_reason: StateReason,
        state_reason_data: StateReasonData = None,
        **kwargs,
    ) -> None:
        if state_value not in ("OK", "ALARM", "INSUFFICIENT_DATA"):
            raise ValidationException(
                f"1 validation error detected: Value '{state_value}' at 'stateValue' failed to satisfy constraint: Member must satisfy enum value set: [INSUFFICIENT_DATA, ALARM, OK]"
            )

        try:
            if state_reason_data:
                state_reason_data = json.loads(state_reason_data)
        except ValueError:
            raise InvalidParameterValueException(
                "TODO: check right error message: Json was not correctly formatted"
            )
        with _STORE_LOCK:
            store = self.get_store(context.account_id, context.region)
            alarm = store.alarms.get(
                arns.cloudwatch_alarm_arn(
                    alarm_name, account_id=context.account_id, region_name=context.region
                )
            )
            if not alarm:
                raise ResourceNotFound()

            old_state = alarm.alarm["StateValue"]

            old_state_reason = alarm.alarm["StateReason"]
            old_state_update_timestamp = alarm.alarm["StateUpdatedTimestamp"]

            if old_state == state_value:
                return

            alarm.alarm["StateTransitionedTimestamp"] = datetime.datetime.now(datetime.UTC)
            # update startDate (=last ALARM date) - should only update when a new alarm is triggered
            # the date is only updated if we have a reason-data, which is set by an alarm
            if state_reason_data:
                state_reason_data["startDate"] = state_reason_data.get("queryDate")

            self._update_state(
                context,
                alarm,
                state_value,
                state_reason,
                state_reason_data,
            )

            self._evaluate_composite_alarms(context, alarm)

            if not alarm.alarm["ActionsEnabled"]:
                return
            if state_value == "OK":
                actions = alarm.alarm["OKActions"]
            elif state_value == "ALARM":
                actions = alarm.alarm["AlarmActions"]
            else:
                actions = alarm.alarm["InsufficientDataActions"]
            for action in actions:
                data = arns.parse_arn(action)
                # test for sns - can this be done in a more generic way?
                if data["service"] == "sns":
                    service = connect_to(
                        region_name=data["region"], aws_access_key_id=data["account"]
                    ).sns
                    subject = f"""{state_value}: "{alarm_name}" in {context.region}"""
                    message = create_message_response_update_state_sns(alarm, old_state)
                    service.publish(TopicArn=action, Subject=subject, Message=message)
                elif data["service"] == "lambda":
                    service = connect_to(
                        region_name=data["region"], aws_access_key_id=data["account"]
                    ).lambda_
                    message = create_message_response_update_state_lambda(
                        alarm, old_state, old_state_reason, old_state_update_timestamp
                    )
                    service.invoke(FunctionName=lambda_function_name(action), Payload=message)
                else:
                    # TODO: support other actions
                    LOG.warning(
                        "Action for service %s not implemented, action '%s' will not be triggered.",
                        data["service"],
                        action,
                    )