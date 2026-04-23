def capture(stack_name: str) -> dict:
        per_resource_events = defaultdict(list)
        events = capture_resource_state_changes(stack_name)
        for event in events:
            if logical_resource_id := event.get("LogicalResourceId"):
                resource_name = (
                    logical_resource_id
                    if logical_resource_id != event.get("StackName")
                    else "Stack"
                )
                normalized_event = normalize_event(event)
                per_resource_events[resource_name].append(normalized_event)

        for resource_id in per_resource_events:
            per_resource_events[resource_id].sort(key=lambda event: event["Timestamp"])

        filtered_per_resource_events = {}
        for resource_id in per_resource_events:
            events = []
            last: tuple[str, str, str] | None = None

            for event in per_resource_events[resource_id]:
                unique_key = (
                    event["LogicalResourceId"],
                    event["ResourceStatus"],
                    event["ResourceType"],
                )
                if last is None:
                    events.append(event)
                    last = unique_key
                    continue

                if unique_key == last:
                    continue

                events.append(event)
                last = unique_key

            filtered_per_resource_events[resource_id] = events

        return filtered_per_resource_events