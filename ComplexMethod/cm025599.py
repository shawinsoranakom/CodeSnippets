def _parse_see_args(message, subscribe_topic):
    """Parse the OwnTracks location parameters, into the format see expects.

    Async friendly.
    """
    user, device = _parse_topic(message["topic"], subscribe_topic)
    dev_id = slugify(f"{user}_{device}")
    kwargs = {"dev_id": dev_id, "host_name": user, "attributes": {}}
    if message["lat"] is not None and message["lon"] is not None:
        kwargs["gps"] = (message["lat"], message["lon"])
    else:
        kwargs["gps"] = None

    if "acc" in message:
        kwargs["gps_accuracy"] = message["acc"]
    if "batt" in message:
        kwargs["battery"] = message["batt"]
    if "vel" in message:
        kwargs["attributes"]["velocity"] = message["vel"]
    if "tid" in message:
        kwargs["attributes"]["tid"] = message["tid"]
    if "addr" in message:
        kwargs["attributes"]["address"] = message["addr"]
    if "cog" in message:
        kwargs["attributes"]["course"] = message["cog"]
    if "bs" in message:
        kwargs["attributes"]["battery_status"] = message["bs"]
    if "t" in message:
        if message["t"] in ("c", "u"):
            kwargs["source_type"] = SourceType.GPS
        if message["t"] == "b":
            kwargs["source_type"] = SourceType.BLUETOOTH_LE

    return dev_id, kwargs