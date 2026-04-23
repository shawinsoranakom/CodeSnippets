def add_permission(self, label: str, actions: list[str], account_ids: list[str]) -> None:
        """
        Create / append to a policy for usage with the add_permission api call

        :param actions: List of actions to be included in the policy, without the SQS: prefix
        :param account_ids: List of account ids to be included in the policy
        :param label: Permission label
        """
        statement = {
            "Sid": label,
            "Effect": "Allow",
            "Principal": {
                "AWS": [
                    f"arn:{get_partition(self.region)}:iam::{account_id}:root"
                    for account_id in account_ids
                ]
                if len(account_ids) > 1
                else f"arn:{get_partition(self.region)}:iam::{account_ids[0]}:root"
            },
            "Action": [f"SQS:{action}" for action in actions]
            if len(actions) > 1
            else f"SQS:{actions[0]}",
            "Resource": self.arn,
        }
        if policy := self.attributes.get(QueueAttributeName.Policy):
            policy = json.loads(policy)
            policy.setdefault("Statement", [])
        else:
            policy = {
                "Version": "2008-10-17",
                "Id": f"{self.arn}/SQSDefaultPolicy",
                "Statement": [],
            }
        policy.setdefault("Statement", [])
        existing_statement_ids = [statement.get("Sid") for statement in policy["Statement"]]
        if label in existing_statement_ids:
            raise InvalidParameterValueException(
                f"Value {label} for parameter Label is invalid. Reason: Already exists."
            )
        policy["Statement"].append(statement)
        self.attributes[QueueAttributeName.Policy] = json.dumps(policy)