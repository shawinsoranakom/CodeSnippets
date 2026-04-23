def check_message(
    sqs_client,
    expected_queue_url,
    expected_topic_arn,
    expected_new,
    expected_reason,
    alarm_name,
    alarm_description,
    expected_trigger,
):
    receive_result = sqs_client.receive_message(QueueUrl=expected_queue_url)
    message = None
    for msg in receive_result["Messages"]:
        body = json.loads(msg["Body"])
        if body["TopicArn"] == expected_topic_arn:
            message = json.loads(body["Message"])
            receipt_handle = msg["ReceiptHandle"]
            sqs_client.delete_message(QueueUrl=expected_queue_url, ReceiptHandle=receipt_handle)
            break
    assert message["NewStateValue"] == expected_new
    assert message["NewStateReason"] == expected_reason
    assert message["AlarmName"] == alarm_name
    assert message["AlarmDescription"] == alarm_description
    assert message["Trigger"] == expected_trigger
    return message