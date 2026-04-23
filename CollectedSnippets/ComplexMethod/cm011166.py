def _all_gather(obj, worker_names=None, timeout: float = UNSET_RPC_TIMEOUT):
    r"""
    This is similar to torch.distributed.all_gather(), but is using RPC. It
    picks the worker with the smallest name (alphabetic order) as the leader.
    Then all followers send their data ``obj`` to the leader. After the leader
    has received all, it will broadcast the results back to all followers. This
    function blocks until all workers have received the gathered results.
    """
    if not worker_names:
        if _ALL_WORKER_NAMES is None:
            raise AssertionError(
                "`_ALL_WORKER_NAMES` is not initialized for `def _all_gather`."
            )
        worker_names = _ALL_WORKER_NAMES
    leader_name = min(worker_names)

    self_name = _get_current_rpc_agent().get_worker_info().name

    with _all_gather_dict_lock:
        concat_names = "".join(sorted(worker_names))
        sequence_num = _all_gather_sequence_id.get(concat_names, 0)
        _all_gather_sequence_id[concat_names] = sequence_num + 1
        sequence_id = concat_names + str(sequence_num)

    is_leader = leader_name == self_name

    if timeout == UNSET_RPC_TIMEOUT:
        # Timeout is specified by agent for RPC calls
        rpc_timeout = get_rpc_timeout()
        # No timeout for signal
        signal_timeout = None
    elif timeout == DEFAULT_SHUTDOWN_TIMEOUT:
        # No timeout for RPC
        rpc_timeout = timeout
        # No timeout for signal
        signal_timeout = None
    else:
        # Signal and RPC timeout use the same timeout
        signal_timeout = rpc_timeout = timeout

    # Phase 1: Followers send it's object to the leader
    if is_leader:
        _gather_to_leader(sequence_id, self_name, obj, worker_names)
    else:
        rpc_sync(
            leader_name,
            _gather_to_leader,
            args=(sequence_id, self_name, obj, worker_names),
            timeout=rpc_timeout,
        )

    with _all_gather_dict_lock:
        states = _all_gather_sequence_id_to_states[sequence_id]

    # Timeout is either set by function parameter or None (which is indefinite)
    states.proceed_signal.wait(timeout=signal_timeout)

    # Phase 2: Leader broadcast gathered results to all followers
    # Leader's signal is the first to be unblocked, after receiving all
    # followers' data objects.
    if is_leader:
        worker_name_to_response_future_dict = {}
        for follower_name in worker_names - {leader_name}:
            fut = rpc_async(
                follower_name,
                _broadcast_to_followers,
                args=(sequence_id, states.gathered_objects),
                timeout=rpc_timeout,
            )
            worker_name_to_response_future_dict[follower_name] = fut

        errors = []
        for follower_name, fut in worker_name_to_response_future_dict.items():
            try:
                fut.wait()
            except RuntimeError as ex:
                errors.append((follower_name, ex))

        if errors:
            raise RuntimeError(
                f"Followers {[e[0] for e in errors]} timed out in _all_gather "
                f"after {rpc_timeout:.2f} seconds. The first exception is {errors[0][1]}"
            )

    # Clean up for the states using the sequence_id
    with _all_gather_dict_lock:
        states = _all_gather_sequence_id_to_states.pop(sequence_id)
    return states.gathered_objects