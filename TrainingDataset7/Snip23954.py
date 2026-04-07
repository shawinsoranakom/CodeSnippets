def wait_or_fail(event, message):
            if not event.wait(5):
                raise AssertionError(message)