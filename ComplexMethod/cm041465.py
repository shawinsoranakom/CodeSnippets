def test_object_created_and_object_removed(
        self,
        s3_bucket,
        sqs_create_queue,
        s3_create_sqs_bucket_notification,
        snapshot,
        aws_client,
    ):
        snapshot.add_transformer(snapshot.transform.sqs_api())
        snapshot.add_transformer(snapshot.transform.s3_api())
        snapshot.add_transformer(snapshot.transform.jsonpath("$..s3.object.key", "object-key"))

        # setup fixture
        queue_url = sqs_create_queue()
        s3_create_sqs_bucket_notification(
            s3_bucket, queue_url, ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
        )

        src_key = f"src-dest-{short_uid()}"
        dest_key = f"key-dest-{short_uid()}"

        # event0 = PutObject
        aws_client.s3.put_object(Bucket=s3_bucket, Key=src_key, Body="something")
        # event1 = CopyObject
        aws_client.s3.copy_object(
            Bucket=s3_bucket,
            CopySource={"Bucket": s3_bucket, "Key": src_key},
            Key=dest_key,
        )
        # event3 = DeleteObject
        aws_client.s3.delete_object(Bucket=s3_bucket, Key=src_key)

        # collect events
        events = sqs_collect_s3_events(aws_client.sqs, queue_url, 3)
        assert len(events) == 3, f"unexpected number of events in {events}"

        # order seems not be guaranteed - sort so we can rely on the order
        events.sort(key=lambda x: x["eventName"])

        snapshot.match("receive_messages", {"messages": events})

        assert events[1]["eventName"] == "ObjectCreated:Put"
        assert events[1]["s3"]["bucket"]["name"] == s3_bucket
        assert events[1]["s3"]["object"]["key"] == src_key

        assert events[0]["eventName"] == "ObjectCreated:Copy"
        assert events[0]["s3"]["bucket"]["name"] == s3_bucket
        assert events[0]["s3"]["object"]["key"] == dest_key

        assert events[2]["eventName"] == "ObjectRemoved:Delete"
        assert events[2]["s3"]["bucket"]["name"] == s3_bucket
        assert events[2]["s3"]["object"]["key"] == src_key