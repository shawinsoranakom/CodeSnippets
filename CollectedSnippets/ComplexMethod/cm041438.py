def check_composite_alarm_message(
    sqs_client,
    queue_url,
    expected_topic_arn,
    alarm_name,
    alarm_description,
    expected_state,
    expected_triggering_child_arn,
    expected_triggering_child_state,
):
    receive_result = sqs_client.receive_message(QueueUrl=queue_url)
    message = None
    for msg in receive_result["Messages"]:
        body = json.loads(msg["Body"])
        if body["TopicArn"] == expected_topic_arn:
            message = json.loads(body["Message"])
            receipt_handle = msg["ReceiptHandle"]
            sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
            break
    assert message["NewStateValue"] == expected_state
    assert message["AlarmName"] == alarm_name
    assert message["AlarmDescription"] == alarm_description
    triggering_child_alarm = message["TriggeringChildren"][0]
    assert triggering_child_alarm["Arn"] == expected_triggering_child_arn
    assert triggering_child_alarm["State"]["Value"] == expected_triggering_child_state
    return message