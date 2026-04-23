def test_object_created_put(
        self,
        s3_bucket,
        sqs_create_queue,
        sns_create_topic,
        sns_create_sqs_subscription,
        snapshot,
        aws_client,
    ):
        snapshot.add_transformer(snapshot.transform.sqs_api())
        snapshot.add_transformer(snapshot.transform.sns_api())
        snapshot.add_transformer(snapshot.transform.s3_api())

        topic_arn = sns_create_topic()["TopicArn"]
        queue_url = sqs_create_queue()
        key_name = "bucket-key"

        # connect topic to queue
        sns_create_sqs_subscription(topic_arn, queue_url)
        create_sns_bucket_notification(
            aws_client.s3, aws_client.sns, s3_bucket, topic_arn, ["s3:ObjectCreated:*"]
        )

        # trigger the events
        aws_client.s3.put_object(Bucket=s3_bucket, Key=key_name, Body="first event")
        aws_client.s3.put_object(Bucket=s3_bucket, Key=key_name, Body="second event")

        # collect messages
        messages = sqs_collect_sns_messages(aws_client.sqs, queue_url, 2)
        # order seems not be guaranteed - sort so we can rely on the order
        messages.sort(key=lambda x: json.loads(x["Message"])["Records"][0]["s3"]["object"]["size"])
        snapshot.match("receive_messages", {"messages": messages})
        # asserts
        # first event
        message = messages[0]
        assert message["Type"] == "Notification"
        assert message["TopicArn"] == topic_arn
        assert message["Subject"] == "Amazon S3 Notification"

        event = json.loads(message["Message"])["Records"][0]
        assert event["eventSource"] == "aws:s3"
        assert event["eventName"] == "ObjectCreated:Put"
        assert event["s3"]["bucket"]["name"] == s3_bucket
        assert event["s3"]["object"]["key"] == key_name
        assert event["s3"]["object"]["size"] == len("first event")

        # second event
        message = messages[1]
        assert message["Type"] == "Notification"
        assert message["TopicArn"] == topic_arn
        assert message["Subject"] == "Amazon S3 Notification"

        event = json.loads(message["Message"])["Records"][0]
        assert event["eventSource"] == "aws:s3"
        assert event["eventName"] == "ObjectCreated:Put"
        assert event["s3"]["bucket"]["name"] == s3_bucket
        assert event["s3"]["object"]["key"] == key_name
        assert event["s3"]["object"]["size"] == len("second event")