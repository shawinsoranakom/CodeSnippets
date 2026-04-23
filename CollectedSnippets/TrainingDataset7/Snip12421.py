async def asend():
                async_responses = await _run_parallel(
                    *(
                        asend_and_wrap_exception(receiver)
                        for receiver in async_receivers
                    )
                )
                return zip(async_receivers, async_responses)