def _enqueue_message(msg: ForwardMsg_pb2.ForwardMsg) -> None:
    """Enqueues a ForwardMsg proto to send to the app."""
    ctx = get_script_run_ctx()

    if ctx is None:
        raise NoSessionContext()

    ctx.enqueue(msg)