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