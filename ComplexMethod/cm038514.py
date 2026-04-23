def get_finished(
        self, finished_req_ids_from_engine: set[str]
    ) -> tuple[set[str] | None, set[str] | None]:
        """
        Check and get the finished store and retrieve requests.

        Args:
            finished_req_ids_from_engine: the set of request ids that are
                reported as finished from the vLLM engine side.

        Returns:
            A tuple of two sets:
            - The first set contains the finished store request ids. The returned
                store request ids MUST be seen before in the
                `finished_req_ids_from_engine`.
            - The second set contains the finished retrieve request ids.

        Notes:
            When enabling async scheduling in vLLM, the same request ID may appear
            multiple times in `finished_req_ids_from_engine`. The adapter should
            take care of deduplicating the request IDs and only return the request
            IDs that have not been returned before.
        """
        finished_stores = set()
        finished_retrieves = set()
        for request_id, (s_future, other_reqs) in self.store_futures.items():
            if not s_future.query():
                continue

            s_result = s_future.result()
            finished_stores.add(request_id)
            finished_stores.update(other_reqs)

            if not s_result:
                # TODO: add error handling here
                logger.error(
                    "Something went wrong when processing the "
                    "store request for request_id=%s",
                    request_id,
                )

        for request_id, (r_future, other_reqs) in self.retrieve_futures.items():
            if not r_future.query():
                continue

            r_result = r_future.result()
            finished_retrieves.add(request_id)
            finished_retrieves.update(other_reqs)

            if not all(r_result):
                # TODO: add error handing here
                logger.error(
                    "Something went wrong when processing the "
                    "retrieve request for request_id=%s, result=%s",
                    request_id,
                    r_result,
                )

        # Remove the finished requests from the tracking dicts
        for request_id in finished_stores:
            self.store_futures.pop(request_id, None)
        for request_id in finished_retrieves:
            self.retrieve_futures.pop(request_id, None)

        # Update the internal states
        self.finished_stores.update(finished_stores)

        ret_stores = set()
        for req_id in finished_req_ids_from_engine:
            if req_id in self.finished_stores or req_id in self.store_futures:
                self.previously_finished.add(req_id)
            else:
                ret_stores.add(req_id)

        # Calculate the final finished stores
        ret_stores.update(self._update_and_get_finished_store())

        return ret_stores, finished_retrieves