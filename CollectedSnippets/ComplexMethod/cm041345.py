def test_create_sns_message_body(self, subscriber):
        message_ctx = SnsMessage(
            message="msg",
            type="Notification",
        )
        result_str = create_sns_message_body(message_ctx, subscriber)
        result = json.loads(result_str)
        try:
            uuid.UUID(result.pop("MessageId"))
        except KeyError:
            raise AssertionError("MessageId missing in SNS response message body")
        except ValueError:
            raise AssertionError("SNS response MessageId not a valid UUID")

        try:
            dateutil.parser.parse(result.pop("Timestamp"))
        except KeyError:
            raise AssertionError("Timestamp missing in SNS response message body")
        except ValueError:
            raise AssertionError("SNS response Timestamp not a valid ISO 8601 date")

        try:
            base64.b64decode(result.pop("Signature"))
        except KeyError:
            raise AssertionError("Signature missing in SNS response message body")
        except ValueError:
            raise AssertionError("SNS response Signature is not a valid base64 encoded value")

        expected_sns_body = {
            "Message": "msg",
            "SignatureVersion": "1",
            "SigningCertURL": "http://localhost.localstack.cloud:4566/_aws/sns/SimpleNotificationService-6c6f63616c737461636b69736e696365.pem",
            "TopicArn": "arn",
            "Type": "Notification",
            "UnsubscribeURL": f"http://localhost.localstack.cloud:4566/?Action=Unsubscribe&SubscriptionArn={subscriber['SubscriptionArn']}",
        }

        assert expected_sns_body == result

        # Now add a subject and message attributes
        message_attributes = {
            "attr1": {
                "DataType": "String",
                "StringValue": "value1",
            },
            "attr2": {
                "DataType": "Binary",
                "BinaryValue": b"\x02\x03\x04",
            },
        }
        message_ctx = SnsMessage(
            type="Notification",
            message="msg",
            subject="subject",
            message_attributes=message_attributes,
        )
        result_str = create_sns_message_body(message_ctx, subscriber)
        result = json.loads(result_str)
        del result["MessageId"]
        del result["Timestamp"]
        del result["Signature"]
        msg = {
            "Message": "msg",
            "Subject": "subject",
            "SignatureVersion": "1",
            "SigningCertURL": "http://localhost.localstack.cloud:4566/_aws/sns/SimpleNotificationService-6c6f63616c737461636b69736e696365.pem",
            "TopicArn": "arn",
            "Type": "Notification",
            "UnsubscribeURL": f"http://localhost.localstack.cloud:4566/?Action=Unsubscribe&SubscriptionArn={subscriber['SubscriptionArn']}",
            "MessageAttributes": {
                "attr1": {
                    "Type": "String",
                    "Value": "value1",
                },
                "attr2": {
                    "Type": "Binary",
                    "Value": b64encode(b"\x02\x03\x04").decode("utf-8"),
                },
            },
        }
        assert msg == result