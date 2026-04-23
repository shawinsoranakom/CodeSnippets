def fake_next(*args, **kwargs):
                test_result.shouldStop = True
                return (0, remote_result.events)