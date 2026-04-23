def test_is_sqs_queue_url():
    # General cases
    assert is_sqs_queue_url("http://localstack.cloud") is False
    assert is_sqs_queue_url("https://localstack.cloud:4566") is False
    assert is_sqs_queue_url("local.localstack.cloud:4566") is False

    # Without proto prefix
    assert (
        is_sqs_queue_url("sqs.us-east-1.localhost.localstack.cloud:4566/111111111111/foo") is True
    )
    assert (
        is_sqs_queue_url("us-east-1.queue.localhost.localstack.cloud:4566/111111111111/foo") is True
    )
    assert is_sqs_queue_url("localhost:4566/queue/ap-south-1/222222222222/bar") is True
    assert is_sqs_queue_url("localhost:4566/111111111111/bar") is True

    # With proto prefix
    assert (
        is_sqs_queue_url(
            "http://sqs.us-east-1.localhost.localstack.cloud:4566/111111111111/foo.fifo"
        )
        is True
    )
    assert (
        is_sqs_queue_url("http://us-east-1.queue.localhost.localstack.cloud:4566/111111111111/foo1")
        is True
    )
    assert is_sqs_queue_url("http://localhost:4566/queue/ap-south-1/222222222222/my-queue") is True
    assert is_sqs_queue_url("http://localhost:4566/111111111111/bar") is True

    # Path strategy uses any domain name
    assert is_sqs_queue_url("foo.bar:4566/queue/ap-south-1/222222222222/bar") is True
    # Domain strategy may omit region
    assert is_sqs_queue_url("http://queue.localhost.localstack.cloud:4566/111111111111/foo") is True

    # Custom domain name
    assert is_sqs_queue_url("http://foo.bar:4566/queue/us-east-1/111111111111/foo") is True
    assert is_sqs_queue_url("http://us-east-1.queue.foo.bar:4566/111111111111/foo") is True
    assert is_sqs_queue_url("http://queue.foo.bar:4566/111111111111/foo") is True
    assert is_sqs_queue_url("http://sqs.us-east-1.foo.bar:4566/111111111111/foo") is True