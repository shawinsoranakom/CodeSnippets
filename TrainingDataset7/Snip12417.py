async def asend():
                async_responses = await _run_parallel(
                    *(
                        receiver(signal=self, sender=sender, **named)
                        for receiver in async_receivers
                    )
                )
                return zip(async_receivers, async_responses)