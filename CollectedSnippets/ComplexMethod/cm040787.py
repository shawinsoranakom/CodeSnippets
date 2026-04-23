def add_permission(
        self,
        context: RequestContext,
        topic_arn: topicARN,
        label: label,
        aws_account_id: DelegatesList,
        action_name: ActionsList,
        **kwargs,
    ) -> None:
        topic: Topic = self._get_topic(topic_arn, context)
        policy = json.loads(topic["attributes"]["Policy"])
        statement = next(
            (statement for statement in policy["Statement"] if statement["Sid"] == label),
            None,
        )

        if statement:
            raise InvalidParameterException("Invalid parameter: Statement already exists")

        if any(action not in VALID_POLICY_ACTIONS for action in action_name):
            raise InvalidParameterException(
                "Invalid parameter: Policy statement action out of service scope!"
            )

        principals = [
            f"arn:{get_partition(context.region)}:iam::{account_id}:root"
            for account_id in aws_account_id
        ]
        actions = [f"SNS:{action}" for action in action_name]

        statement = {
            "Sid": label,
            "Effect": "Allow",
            "Principal": {"AWS": principals[0] if len(principals) == 1 else principals},
            "Action": actions[0] if len(actions) == 1 else actions,
            "Resource": topic_arn,
        }

        policy["Statement"].append(statement)
        topic["attributes"]["Policy"] = json.dumps(policy)