def filter_alloc_free_pairs(data):
    for dev_id in range(len(data["device_traces"])):
        # set of indexes of trace events for alloc-free pairs
        filterSet = set()
        # map from addr to index of alloc event
        allocMap = {}
        # set of addrs from free_requested events
        freeRequested = set()
        for idx, event in enumerate(data["device_traces"][dev_id]):
            if event["action"] == "alloc":
                allocMap[event["addr"]] = idx
            elif event["action"] == "free_requested":
                freeRequested.add(event["addr"])
                if allocMap.get(event["addr"]) is not None:
                    filterSet.add(idx)
                    filterSet.add(allocMap[event["addr"]])
                    allocMap.pop(event["addr"])
            elif event["action"] == "free_completed":
                if event["addr"] in freeRequested:
                    freeRequested.remove(event["addr"])
                    filterSet.add(idx)
                else:
                    print(f"free_completed without free_requested: {event}")

        # Remove events whose index is in filterSet
        if filterSet:
            # Create a new list excluding events with indices in filterSet
            data["device_traces"][dev_id] = [
                event
                for idx, event in enumerate(data["device_traces"][dev_id])
                if idx not in filterSet
            ]

    return data