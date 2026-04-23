def enqueue_deltas(container: int, path: Tuple[int, ...]):
            # We deep-copy the protos because we mutate each one
            # multiple times.
            msg = copy.deepcopy(TEXT_DELTA_MSG1)
            msg.metadata.delta_path[:] = make_delta_path(container, path, 0)
            rq.enqueue(msg)

            msg = copy.deepcopy(DF_DELTA_MSG)
            msg.metadata.delta_path[:] = make_delta_path(container, path, 1)
            rq.enqueue(msg)

            msg = copy.deepcopy(ADD_ROWS_MSG)
            msg.metadata.delta_path[:] = make_delta_path(container, path, 1)
            rq.enqueue(msg)