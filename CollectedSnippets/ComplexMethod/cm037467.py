def abort_requests(self, request_ids: Iterable[str], internal: bool) -> list[str]:
        """Abort a list of requests.

        The request_ids may be either external request IDs (those passed to
        InputProcessor.process_inputs()) or internal request IDs (those randomly
        generated when creating the EngineCoreRequest).

        If an external request ID is provided, and that external request ID
        was used for multiple requests, all requests associated with that external
        request ID are aborted.

        In the case of parallel sampling, a request ID may be used to identify
        a parent request, in which case the associated child requests are aborted
        also.
        """
        internal_req_ids = []
        for request_id in request_ids:
            if internal:
                # Internal ID - this may be a parent request
                internal_req_ids.append(request_id)

                # Remove internal ID from the external->internal mapping
                if req_state := self.request_states.get(request_id):
                    external_req_id = req_state.external_req_id
                    internal_ids = self.external_req_ids[external_req_id]
                    internal_ids.remove(request_id)
                    if not internal_ids:
                        del self.external_req_ids[external_req_id]
            elif internal_ids := self.external_req_ids.pop(request_id, []):
                # External ID - abort all requests in the external->internal mapping
                internal_req_ids.extend(internal_ids)

        request_ids_to_abort = []
        for request_id in internal_req_ids:
            req_state = self.request_states.pop(request_id, None)
            if req_state is not None:
                self.lora_states.request_finished(request_id, req_state.lora_name)
                request_ids_to_abort.append(request_id)
                # Produce final abort output.
                if req_state.queue is not None and (
                    request_output := req_state.make_request_output(
                        new_token_ids=[],
                        # Set pooling_output is not None to
                        # correctly enter the abort pooling branch
                        pooling_output=EMPTY_CPU_TENSOR
                        if req_state.detokenizer is None
                        else None,
                        finish_reason=FinishReason.ABORT,
                        stop_reason=None,
                        kv_transfer_params=None,
                    )
                ):
                    req_state.queue.put(request_output)
            elif parent := self.parent_requests.get(request_id):
                # Abort children prior to removing the parent.
                if parent.child_requests:
                    child_reqs = list(parent.child_requests)
                    child_reqs = self.abort_requests(child_reqs, internal=True)
                    request_ids_to_abort.extend(child_reqs)
                self.parent_requests.pop(request_id, None)
        return request_ids_to_abort