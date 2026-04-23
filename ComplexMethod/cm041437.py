def deserialize_event(event):
    # Deserialize into Python dictionary and extract the "NewImage" (the new version of the full ddb document)
    ddb = event.get("dynamodb")
    if ddb:
        result = {
            "__action_type": event.get("eventName"),
        }

        ddb_deserializer = TypeDeserializer()
        if ddb.get("OldImage"):
            result["old_image"] = ddb_deserializer.deserialize({"M": ddb.get("OldImage")})
        if ddb.get("NewImage"):
            result["new_image"] = ddb_deserializer.deserialize({"M": ddb.get("NewImage")})

        return result
    kinesis = event.get("kinesis")
    if kinesis:
        assert kinesis["sequenceNumber"]
        kinesis["data"] = json.loads(to_str(base64.b64decode(kinesis["data"])))
        return kinesis
    sqs = event.get("sqs")
    if sqs:
        result = {"data": event["body"]}
        return result
    sns = event.get("Sns")
    if sns:
        result = {"data": sns["Message"]}
        return result