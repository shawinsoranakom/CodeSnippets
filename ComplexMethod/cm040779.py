def publish_batch_to_topic(self, ctx: SnsBatchPublishContext, topic_arn: str) -> None:
        subscriptions = get_topic_subscriptions(ctx.store, topic_arn)
        for subscriber in subscriptions:
            protocol = subscriber["Protocol"]
            notifier = self.batch_topic_notifiers.get(protocol)
            # does the notifier supports batching natively? for now, only SQS supports it
            if notifier:
                subscriber_ctx = ctx
                messages_amount_before_filtering = len(ctx.messages)
                filtered_messages = [
                    message
                    for message in ctx.messages
                    if self._should_publish(
                        ctx.store.subscription_filter_policy, message, subscriber
                    )
                ]
                if not filtered_messages:
                    LOG.debug(
                        "No messages match filter policy, not publishing batch from topic '%s' to subscription '%s'",
                        topic_arn,
                        subscriber["SubscriptionArn"],
                    )
                    continue

                messages_amount = len(filtered_messages)
                if messages_amount != messages_amount_before_filtering:
                    LOG.debug(
                        "After applying subscription filter, %s out of %s message(s) to be sent to '%s'",
                        messages_amount,
                        messages_amount_before_filtering,
                        subscriber["SubscriptionArn"],
                    )
                    # We need to copy the context to not overwrite the messages after filtering messages, otherwise we
                    # would filter on the same context for different subscribers
                    subscriber_ctx = copy.copy(ctx)
                    subscriber_ctx.messages = filtered_messages

                LOG.debug(
                    "Topic '%s' batch publishing %s messages to subscribed '%s' with protocol '%s' (subscription '%s')",
                    topic_arn,
                    messages_amount,
                    subscriber.get("Endpoint"),
                    subscriber["Protocol"],
                    subscriber["SubscriptionArn"],
                )
                self._submit_notification(notifier, subscriber_ctx, subscriber)
            else:
                # if no batch support, fall back to sending them sequentially
                notifier = self.topic_notifiers[subscriber["Protocol"]]
                for message in ctx.messages:
                    if self._should_publish(
                        ctx.store.subscription_filter_policy, message, subscriber
                    ):
                        individual_ctx = SnsPublishContext(
                            message=message, store=ctx.store, request_headers=ctx.request_headers
                        )
                        LOG.debug(
                            "Topic '%s' batch publishing '%s' to subscribed '%s' with protocol '%s' (subscription '%s')",
                            topic_arn,
                            individual_ctx.message.message_id,
                            subscriber.get("Endpoint"),
                            subscriber["Protocol"],
                            subscriber["SubscriptionArn"],
                        )
                        self._submit_notification(notifier, individual_ctx, subscriber)