def get_state(data: dict[str, float], key: str) -> str | float:
    """Get current download/upload state."""
    upload = data[DelugeGetSessionStatusKeys.UPLOAD_RATE.value]
    download = data[DelugeGetSessionStatusKeys.DOWNLOAD_RATE.value]
    protocol_upload = data[DelugeGetSessionStatusKeys.DHT_UPLOAD_RATE.value]
    protocol_download = data[DelugeGetSessionStatusKeys.DHT_DOWNLOAD_RATE.value]

    # if key is CURRENT_STATUS, we just return whether we are uploading / downloading / idle
    if key == DelugeSensorType.CURRENT_STATUS_SENSOR:
        if upload > 0 and download > 0:
            return "seeding_and_downloading"
        if upload > 0 and download == 0:
            return "seeding"
        if upload == 0 and download > 0:
            return "downloading"
        return STATE_IDLE

    # if not, return the transfer rate for the given key
    rate = 0.0
    if key == DelugeSensorType.DOWNLOAD_SPEED_SENSOR:
        rate = download
    elif key == DelugeSensorType.UPLOAD_SPEED_SENSOR:
        rate = upload
    elif key == DelugeSensorType.PROTOCOL_TRAFFIC_DOWNLOAD_SPEED_SENSOR:
        rate = protocol_download
    else:
        rate = protocol_upload

    # convert to KiB/s and round
    kb_spd = rate / 1024
    return round(kb_spd, 2 if kb_spd < 0.1 else 1)