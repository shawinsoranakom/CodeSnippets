async def test_disconnected_agent() -> None:
    host_address = "localhost:50060"
    host = GrpcWorkerAgentRuntimeHost(address=host_address)
    host.start()
    worker1 = GrpcWorkerAgentRuntime(host_address=host_address)
    worker1_2 = GrpcWorkerAgentRuntime(host_address=host_address)

    # TODO: Implementing `get_current_subscriptions` and `get_subscribed_recipients` requires access
    # to some private properties. This needs to be updated once they are available publicly

    def get_current_subscriptions() -> List[Subscription]:
        return host._servicer._subscription_manager._subscriptions  # type: ignore[reportPrivateUsage]

    async def get_subscribed_recipients() -> List[AgentId]:
        return await host._servicer._subscription_manager.get_subscribed_recipients(DefaultTopicId())  # type: ignore[reportPrivateUsage]

    try:
        await worker1.start()
        await LoopbackAgentWithDefaultSubscription.register(
            worker1, "worker1", lambda: LoopbackAgentWithDefaultSubscription()
        )

        subscriptions1 = get_current_subscriptions()
        assert len(subscriptions1) == 2
        recipients1 = await get_subscribed_recipients()
        assert AgentId(type="worker1", key="default") in recipients1

        first_subscription_id = subscriptions1[0].id

        await worker1.publish_message(ContentMessage(content="Hello!"), DefaultTopicId())
        # This is a simple simulation of worker disconnct
        if worker1._host_connection is not None:  # type: ignore[reportPrivateUsage]
            try:
                await worker1._host_connection.close()  # type: ignore[reportPrivateUsage]
            except asyncio.CancelledError:
                pass

        await asyncio.sleep(1)

        subscriptions2 = get_current_subscriptions()
        assert len(subscriptions2) == 0
        recipients2 = await get_subscribed_recipients()
        assert len(recipients2) == 0
        await asyncio.sleep(1)

        await worker1_2.start()
        await LoopbackAgentWithDefaultSubscription.register(
            worker1_2, "worker1", lambda: LoopbackAgentWithDefaultSubscription()
        )

        subscriptions3 = get_current_subscriptions()
        assert len(subscriptions3) == 2
        assert first_subscription_id not in [x.id for x in subscriptions3]

        recipients3 = await get_subscribed_recipients()
        assert len(set(recipients2)) == len(recipients2)  # Make sure there are no duplicates
        assert AgentId(type="worker1", key="default") in recipients3
    except Exception as ex:
        raise ex
    finally:
        await worker1.stop()
        await worker1_2.stop()