def test_parse_queue_url_valid():
    assert parse_queue_url("http://localhost:4566/queue/eu-central-2/000000000001/my-queue") == (
        "000000000001",
        "eu-central-2",
        "my-queue",
    )
    assert parse_queue_url("http://localhost:4566/000000000001/my-queue") == (
        "000000000001",
        None,
        "my-queue",
    )
    assert parse_queue_url("http://localhost/000000000001/my-queue") == (
        "000000000001",
        None,
        "my-queue",
    )

    assert parse_queue_url("http://localhost/queue/eu-central-2/000000000001/my-queue") == (
        "000000000001",
        "eu-central-2",
        "my-queue",
    )

    assert parse_queue_url(
        "http://queue.localhost.localstack.cloud:4566/000000000001/my-queue"
    ) == (
        "000000000001",
        "us-east-1",
        "my-queue",
    )

    assert parse_queue_url(
        "http://eu-central-2.queue.localhost.localstack.cloud:4566/000000000001/my-queue"
    ) == (
        "000000000001",
        "eu-central-2",
        "my-queue",
    )

    # in this case, eu-central-2.foobar... is treated as a regular hostname
    assert parse_queue_url(
        "http://eu-central-2.foobar.localhost.localstack.cloud:4566/000000000001/my-queue"
    ) == (
        "000000000001",
        None,
        "my-queue",
    )