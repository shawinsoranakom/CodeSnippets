def _assert(scheduler: Scheduler) -> None:
            dequeued_slots: list[str] = []
            requests: list[Request] = []
            assert scheduler.crawler
            assert scheduler.crawler.engine
            downloader = scheduler.crawler.engine.downloader
            assert isinstance(downloader, MockDownloader)
            while scheduler.has_pending_requests():
                request = scheduler.next_request()
                assert request is not None
                slot = downloader.get_slot_key(request)
                dequeued_slots.append(slot)
                downloader.increment(slot)
                requests.append(request)

            for request in requests:
                slot = downloader.get_slot_key(request)
                downloader.decrement(slot)

            assert _is_scheduling_fair([s for u, s in _URLS_WITH_SLOTS], dequeued_slots)
            assert sum(len(s.active) for s in downloader.slots.values()) == 0