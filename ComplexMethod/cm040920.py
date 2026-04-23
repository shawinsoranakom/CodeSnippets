def _get_event_payload(
        ctx: S3EventNotificationContext, config_id: NotificationId = None
    ) -> PutEventsRequestEntry:
        # see https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventBridge.html
        # see also https://docs.aws.amazon.com/AmazonS3/latest/userguide/ev-events.html
        partition = get_partition(ctx.region)
        entry: PutEventsRequestEntry = {
            "Source": "aws.s3",
            "Resources": [f"arn:{partition}:s3:::{ctx.bucket_name}"],
            "Time": ctx.event_time,
        }

        if ctx.xray:
            entry["TraceHeader"] = ctx.xray

        event_details = {
            "version": "0",
            "bucket": {"name": ctx.bucket_name},
            "object": {
                "key": ctx.key_name,
                "size": ctx.key_size,
                "etag": ctx.key_etag,
                "sequencer": "0062E99A88DC407460",
            },
            "request-id": ctx.request_id,
            "requester": "074255357339",
            "source-ip-address": "127.0.0.1",
            # TODO previously headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
        }
        if ctx.key_version_id and ctx.key_version_id != "null":
            event_details["object"]["version-id"] = ctx.key_version_id

        if "ObjectCreated" in ctx.event_type:
            entry["DetailType"] = "Object Created"
            event_type = ctx.event_type
            event_action = event_type[event_type.rindex(":") + 1 :]
            if event_action in ["Put", "Post", "Copy"]:
                event_type = f"{event_action}Object"
            # TODO: what about CompleteMultiformUpload??
            event_details["reason"] = event_type

        elif "ObjectRemoved" in ctx.event_type:
            entry["DetailType"] = "Object Deleted"
            event_details["reason"] = "DeleteObject"
            if "DeleteMarkerCreated" in ctx.event_type:
                delete_type = "Delete Marker Created"
            else:
                delete_type = "Permanently Deleted"
                event_details["object"].pop("etag")

            event_details["deletion-type"] = delete_type
            event_details["object"].pop("size")

        elif "ObjectTagging" in ctx.event_type:
            entry["DetailType"] = (
                "Object Tags Added" if "Put" in ctx.event_type else "Object Tags Deleted"
            )

        elif "ObjectAcl" in ctx.event_type:
            entry["DetailType"] = "Object ACL Updated"
            event_details["object"].pop("size")
            event_details["object"].pop("sequencer")

        elif "ObjectRestore" in ctx.event_type:
            entry["DetailType"] = (
                "Object Restore Initiated"
                if "Post" in ctx.event_type
                else "Object Restore Completed"
            )
            event_details["source-storage-class"] = ctx.key_storage_class
            event_details["object"].pop("sequencer", None)
            if ctx.event_type.endswith("Completed"):
                event_details["restore-expiry-time"] = timestamp_millis(ctx.key_expiry)
                event_details.pop("source-ip-address", None)
                # a bit hacky, it is to ensure the eventTime is a bit after the `Post` event, as its instant in LS
                # the best would be to delay the publishing of the event. We need at least 1s as it's the precision
                # of the event
                entry["Time"] = entry["Time"] + datetime.timedelta(seconds=1)

        entry["Detail"] = json.dumps(event_details)
        return entry