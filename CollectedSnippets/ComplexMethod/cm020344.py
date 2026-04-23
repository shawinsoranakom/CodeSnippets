async def async_complete_pubsub_flow(
        self,
        result: dict,
        selected_topic: str,
        selected_subscription: str = "create_new_subscription",
        user_input: dict | None = None,
        existing_errors: dict | None = None,
    ) -> FlowResult:
        """Fixture to walk through the Pub/Sub topic and subscription steps.

        This picks a simple set of steps that are reusable for most flows without
        exercising the corner cases.
        """

        # Validate Pub/Sub topics are shown
        assert result.get("type") is FlowResultType.FORM
        assert result.get("step_id") == "pubsub_topic"
        assert not result.get("errors")

        # Select Pub/Sub topic the show available subscriptions (none)
        result = await self.async_configure(
            result,
            {
                "topic_name": selected_topic,
            },
        )
        assert result.get("type") is FlowResultType.FORM
        assert result.get("step_id") == "pubsub_topic_confirm"
        assert not result.get("errors")

        # ACK the topic selection. User is instructed to do some manual
        result = await self.async_configure(result, {})
        assert result.get("type") is FlowResultType.FORM
        assert result.get("step_id") == "pubsub_subscription"
        assert not result.get("errors")

        # Create the subscription and end the flow
        return await self.async_finish_setup(
            result,
            {
                "subscription_name": selected_subscription,
            },
        )