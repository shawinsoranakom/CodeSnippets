async def asend_and_wrap_exception(receiver):
            try:
                response = await receiver(signal=self, sender=sender, **named)
            except Exception as err:
                self._log_robust_failure(receiver, err)
                return err
            return response