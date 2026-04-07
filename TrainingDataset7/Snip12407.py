def send(self, sender, **named):
        """
        Send signal from sender to all connected receivers.

        If any receiver raises an error, the error propagates back through
        send, terminating the dispatch loop. So it's possible that all
        receivers won't be called if an error is raised.

        If any receivers are asynchronous, they are called after all the
        synchronous receivers via a single call to async_to_sync(). They are
        also executed concurrently with asyncio.TaskGroup().

        Arguments:

            sender
                The sender of the signal. Either a specific object or None.

            named
                Named arguments which will be passed to receivers.

        Return a list of tuple pairs [(receiver, response), ... ].
        """
        if (
            not self.receivers
            or self.sender_receivers_cache.get(sender) is NO_RECEIVERS
        ):
            return []
        responses = []
        sync_receivers, async_receivers = self._live_receivers(sender)
        for receiver in sync_receivers:
            response = receiver(signal=self, sender=sender, **named)
            responses.append((receiver, response))
        if async_receivers:

            async def asend():
                async_responses = await _run_parallel(
                    *(
                        receiver(signal=self, sender=sender, **named)
                        for receiver in async_receivers
                    )
                )
                return zip(async_receivers, async_responses)

            responses.extend(async_to_sync(asend)())
        return responses