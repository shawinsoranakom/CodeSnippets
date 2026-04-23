async def register_instance(
        self,
        runtime: AgentRuntime,
        agent_id: AgentId,
        *,
        skip_class_subscriptions: bool = True,
        skip_direct_message_subscription: bool = False,
    ) -> AgentId:
        """
        This function is similar to `register` but is used for registering an instance of an agent. A subscription based on the agent ID is created and added to the runtime.
        """
        agent_id = await runtime.register_agent_instance(agent_instance=self, agent_id=agent_id)

        id_subscription = TypeSubscription(topic_type=agent_id.key, agent_type=agent_id.type)
        await runtime.add_subscription(id_subscription)

        if not skip_class_subscriptions:
            with SubscriptionInstantiationContext.populate_context(AgentType(agent_id.type)):
                subscriptions: List[Subscription] = []
                for unbound_subscription in self._unbound_subscriptions():
                    subscriptions_list_result = unbound_subscription()
                    if inspect.isawaitable(subscriptions_list_result):
                        subscriptions_list = await subscriptions_list_result
                    else:
                        subscriptions_list = subscriptions_list_result

                    subscriptions.extend(subscriptions_list)
            for subscription in subscriptions:
                await runtime.add_subscription(subscription)

        if not skip_direct_message_subscription:
            # Additionally adds a special prefix subscription for this agent to receive direct messages
            try:
                await runtime.add_subscription(
                    TypePrefixSubscription(
                        # The prefix MUST include ":" to avoid collisions with other agents
                        topic_type_prefix=agent_id.type + ":",
                        agent_type=agent_id.type,
                    )
                )
            except ValueError:
                # We don't care if the subscription already exists
                pass

        # TODO: deduplication
        for _message_type, serializer in self._handles_types():
            runtime.add_message_serializer(serializer)

        return agent_id