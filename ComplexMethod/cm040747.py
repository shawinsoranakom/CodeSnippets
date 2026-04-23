def parse_batch_item_failures(
    result: dict | str | None, valid_item_ids: set[str] | None = None
) -> list[str]:
    """
    Parses a partial batch failure response, that looks like this: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes-batching-concurrency.html

        {
          "batchItemFailures": [
                {
                    "itemIdentifier": "id2"
                },
                {
                    "itemIdentifier": "id4"
                }
            ]
        }

    If the response returns an empty list, then the batch should be considered as a complete success. If an exception
    is raised, the batch should be considered a complete failure.

    Pipes partial batch failure: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-pipes-batching-concurrency.html
    Lambda ESM with SQS: https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html
    Special cases: https://repost.aws/knowledge-center/lambda-sqs-report-batch-item-failures
    Kinesis: https://docs.aws.amazon.com/lambda/latest/dg/services-kinesis-batchfailurereporting.html

    :param result: the process status (e.g., invocation result from Lambda)
    :param valid_item_ids: the set of valid item ids in the batch
    :raises KeyError: if the itemIdentifier value is missing or not in the batch
    :raises Exception: any other exception related to parsing (e.g., JSON parser error)
    :return: a list of item IDs that failed
    """
    if not result:
        return []

    if isinstance(result, dict):
        partial_batch_failure = result
    else:
        partial_batch_failure = json.loads(result)

    if not partial_batch_failure:
        return []

    batch_item_failures = partial_batch_failure.get("batchItemFailures")

    if not batch_item_failures:
        return []

    failed_items = []
    for item in batch_item_failures:
        if "itemIdentifier" not in item:
            raise KeyError(f"missing itemIdentifier in batchItemFailure record {item}")

        item_identifier = item["itemIdentifier"]
        if not item_identifier:
            raise ValueError("itemIdentifier cannot be empty or null")

        # Optionally validate whether the item_identifier is part of the batch
        if valid_item_ids and item_identifier not in valid_item_ids:
            raise KeyError(f"itemIdentifier '{item_identifier}' not in the batch")

        failed_items.append(item_identifier)

    return failed_items