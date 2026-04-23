async def abort_requests_async(self, request_ids: list[str]) -> None:
        if not request_ids or self.resources.engine_dead:
            return

        if len(request_ids) == 1:
            # Fast-path common case.
            if engine := self.reqs_in_flight.get(request_ids[0]):
                await self._abort_requests(request_ids, engine)
            return

        by_engine = defaultdict[EngineIdentity, list[str]](list)
        for req_id in request_ids:
            if engine := self.reqs_in_flight.get(req_id):
                by_engine[engine].append(req_id)
        for engine, req_ids in by_engine.items():
            await self._abort_requests(req_ids, engine)