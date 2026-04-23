def parse_queue_url(queue_url: str) -> tuple[str, str | None, str]:
    """
    Parses an SQS Queue URL and returns a triple of account_id, region and queue_name.

    :param queue_url: the queue URL
    :return: account_id, region (may be None), queue_name
    """
    url = urlparse(queue_url.rstrip("/"))
    path_parts = url.path.lstrip("/").split("/")
    domain_parts = url.netloc.split(".")

    if len(path_parts) != 2 and len(path_parts) != 4:
        raise ValueError(f"Not a valid queue URL: {queue_url}")

    account_id, queue_name = path_parts[-2:]

    if len(path_parts) == 4:
        if path_parts[0] != "queue":
            raise ValueError(f"Not a valid queue URL: {queue_url}")
        # SQS_ENDPOINT_STRATEGY == "path"
        region = path_parts[1]
    elif url.netloc.startswith("sqs."):
        # SQS_ENDPOINT_STRATEGY == "standard"
        region = domain_parts[1]
    elif ".queue." in url.netloc:
        if domain_parts[1] != "queue":
            # .queue. should be on second position after the region
            raise ValueError(f"Not a valid queue URL: {queue_url}")
        # SQS_ENDPOINT_STRATEGY == "domain"
        region = domain_parts[0]
    elif url.netloc.startswith("queue"):
        # SQS_ENDPOINT_STRATEGY == "domain" (with default region)
        region = "us-east-1"
    else:
        region = None

    return account_id, region, queue_name