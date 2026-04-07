def handle_event(self, result, tests, event):
        event_name = event[0]
        handler = getattr(result, event_name, None)
        if handler is None:
            return
        test_index = event[1]
        event_occurred_before_first_test = test_index == -1
        if (
            event_name == "addError"
            and event_occurred_before_first_test
            and len(event) >= 4
        ):
            test_id = event[2]
            test = unittest.suite._ErrorHolder(test_id)
            args = event[3:]
        else:
            test = tests[test_index]
            args = event[2:]
        handler(test, *args)