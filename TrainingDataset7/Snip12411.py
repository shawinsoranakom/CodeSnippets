async def asend_robust(self, sender, **named):
        """
        Send signal from sender to all connected receivers catching errors.

        If any receivers are synchronous, they are grouped and called behind a
        sync_to_async() adaption before executing any asynchronous receivers.

        If any receivers are asynchronous, they are grouped and executed
        concurrently with asyncio.TaskGroup.

        Arguments:

            sender
                The sender of the signal. Can be any Python object (normally
                one registered with a connect if you actually want something to
                occur).

            named
                Named arguments which will be passed to receivers.

        Return a list of tuple pairs [(receiver, response), ... ].

        If any receiver raises an error (specifically any subclass of
        Exception), return the error instance as the result for that receiver.
        """
        if (
            not self.receivers
            or self.sender_receivers_cache.get(sender) is NO_RECEIVERS
        ):
            return []

        # Call each receiver with whatever arguments it can accept.
        # Return a list of tuple pairs [(receiver, response), ... ].
        sync_receivers, async_receivers = self._live_receivers(sender)

        if sync_receivers:

            @sync_to_async
            def sync_send():
                responses = []
                for receiver in sync_receivers:
                    try:
                        response = receiver(signal=self, sender=sender, **named)
                    except Exception as err:
                        self._log_robust_failure(receiver, err)
                        responses.append((receiver, err))
                    else:
                        responses.append((receiver, response))
                return responses

        else:

            async def sync_send():
                return []

        async def asend_and_wrap_exception(receiver):
            try:
                response = await receiver(signal=self, sender=sender, **named)
            except Exception as err:
                self._log_robust_failure(receiver, err)
                return err
            return response

        responses = await sync_send()
        async_responses = await _run_parallel(
            *(asend_and_wrap_exception(receiver) for receiver in async_receivers),
        )
        responses.extend(zip(async_receivers, async_responses))
        return responses