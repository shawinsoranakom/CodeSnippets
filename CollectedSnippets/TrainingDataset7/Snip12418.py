def sync_send():
                responses = []
                for receiver in sync_receivers:
                    response = receiver(signal=self, sender=sender, **named)
                    responses.append((receiver, response))
                return responses