def test_list_queues_multi_region_with_endpoint_strategy_standard(
        self, aws_client_factory, cleanups, monkeypatch
    ):
        monkeypatch.setattr(config, "SQS_ENDPOINT_STRATEGY", "standard")

        region1 = "us-east-1"
        region2 = "eu-central-1"

        region1_client = aws_client_factory(region_name=region1).sqs
        region2_client = aws_client_factory(region_name=region2).sqs

        queue_name = f"queue-{short_uid()}"

        queue1_url = region1_client.create_queue(QueueName=queue_name)["QueueUrl"]
        cleanups.append(lambda: region1_client.delete_queue(QueueUrl=queue1_url))
        queue2_url = region2_client.create_queue(QueueName=queue_name)["QueueUrl"]
        cleanups.append(lambda: region2_client.delete_queue(QueueUrl=queue2_url))

        assert (
            f"sqs.{region1}." in queue1_url
        )  # region is always included irrespective of whether it is us-east-1
        assert f"sqs.{region2}." in queue2_url
        assert region1 not in queue2_url
        assert region2 not in queue1_url

        assert queue1_url in region1_client.list_queues().get("QueueUrls", [])
        assert queue2_url not in region1_client.list_queues().get("QueueUrls", [])

        assert queue1_url not in region2_client.list_queues().get("QueueUrls", [])
        assert queue2_url in region2_client.list_queues().get("QueueUrls", [])