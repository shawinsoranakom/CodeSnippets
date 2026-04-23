def get_subscription_attributes(
        self, context: RequestContext, subscription_arn: subscriptionARN, **kwargs
    ) -> GetSubscriptionAttributesResponse:
        store = self.get_store(account_id=context.account_id, region=context.region)
        sub = store.subscriptions.get(subscription_arn)
        if not sub:
            raise NotFoundException("Subscription does not exist")
        removed_attrs = ["sqs_queue_url"]
        if "FilterPolicyScope" in sub and not sub.get("FilterPolicy"):
            removed_attrs.append("FilterPolicyScope")
            removed_attrs.append("FilterPolicy")
        elif "FilterPolicy" in sub and "FilterPolicyScope" not in sub:
            sub["FilterPolicyScope"] = "MessageAttributes"

        attributes = {k: v for k, v in sub.items() if k not in removed_attrs}
        return GetSubscriptionAttributesResponse(Attributes=attributes)