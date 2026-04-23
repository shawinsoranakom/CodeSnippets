def _msg_dict_from_dcp_method_args(*args, **kwargs) -> dict[str, Any]:
    """
    Extracts log data from dcp method args
    """
    msg_dict = {}

    # checkpoint ID can be passed in through the serializer or through the checkpoint id directly
    storage_writer = kwargs.get("storage_writer")
    storage_reader = kwargs.get("storage_reader")
    planner = kwargs.get("planner")

    checkpoint_id = kwargs.get("checkpoint_id")
    if not checkpoint_id and (serializer := storage_writer or storage_reader):
        checkpoint_id = getattr(serializer, "checkpoint_id", None)

    msg_dict["checkpoint_id"] = (
        # pyrefly: ignore [unsupported-operation]
        str(checkpoint_id) if checkpoint_id is not None else checkpoint_id
    )

    # Uniquely identify a _dcp_method_logger wrapped function call.
    msg_dict["uuid"] = str(uuid4().int)

    if storage_writer:
        msg_dict["storage_writer"] = storage_writer.__class__.__name__

    if storage_reader:
        msg_dict["storage_reader"] = storage_reader.__class__.__name__

    if planner:
        msg_dict["planner"] = planner.__class__.__name__

    return msg_dict