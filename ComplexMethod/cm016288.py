def comparator(a: ShardedTest, b: ShardedTest) -> int:
                    # serial comes first
                    if a.name in serial and b.name not in serial:
                        return -1
                    if a.name not in serial and b.name in serial:
                        return 1
                    # known test times come first
                    if a.time is not None and b.time is None:
                        return -1
                    if a.time is None and b.time is not None:
                        return 1
                    if a.time == b.time:
                        return 0
                    # not None due to the above checks
                    return -1 if a.time > b.time else 1