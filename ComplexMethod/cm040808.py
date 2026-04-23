def validate_event(event: PutEventsRequestEntry) -> None | PutEventsResultEntry:
    if not event.get("Source"):
        return {
            "ErrorCode": "InvalidArgument",
            "ErrorMessage": "Parameter Source is not valid. Reason: Source is a required argument.",
        }
    elif not event.get("DetailType"):
        return {
            "ErrorCode": "InvalidArgument",
            "ErrorMessage": "Parameter DetailType is not valid. Reason: DetailType is a required argument.",
        }
    elif not event.get("Detail"):
        return {
            "ErrorCode": "InvalidArgument",
            "ErrorMessage": "Parameter Detail is not valid. Reason: Detail is a required argument.",
        }
    elif event.get("Detail") and len(event["Detail"]) >= 262144:
        raise ValidationException("Total size of the entries in the request is over the limit.")
    elif event.get("Detail"):
        try:
            json_detail = json.loads(event.get("Detail"))
            if isinstance(json_detail, dict):
                return
        except json.JSONDecodeError:
            pass

        return {
            "ErrorCode": "MalformedDetail",
            "ErrorMessage": "Detail is malformed.",
        }