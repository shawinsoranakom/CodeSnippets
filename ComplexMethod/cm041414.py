def test_account_id_namespacing_for_localstack_backends(self, client_factory):
        # Ensure resources are isolated by account ID namespaces
        account_id1 = "420420420420"
        account_id2 = "133713371337"

        sns_client1 = client_factory("sns", account_id1)
        sns_client2 = client_factory("sns", account_id2)

        arn1 = sns_client1.create_topic(Name="foo")["TopicArn"]

        assert len(sns_client1.list_topics()["Topics"]) == 1
        assert len(sns_client2.list_topics()["Topics"]) == 0

        arn2 = sns_client2.create_topic(Name="foo")["TopicArn"]
        arn3 = sns_client2.create_topic(Name="bar")["TopicArn"]

        assert len(sns_client1.list_topics()["Topics"]) == 1
        assert len(sns_client2.list_topics()["Topics"]) == 2

        sns_client1.tag_resource(ResourceArn=arn1, Tags=[{"Key": "foo", "Value": "1"}])

        assert len(sns_client1.list_tags_for_resource(ResourceArn=arn1)["Tags"]) == 1
        assert len(sns_client2.list_tags_for_resource(ResourceArn=arn2)["Tags"]) == 0
        assert len(sns_client2.list_tags_for_resource(ResourceArn=arn3)["Tags"]) == 0

        sns_client2.tag_resource(ResourceArn=arn2, Tags=[{"Key": "foo", "Value": "1"}])
        sns_client2.tag_resource(ResourceArn=arn2, Tags=[{"Key": "bar", "Value": "1"}])
        sns_client2.tag_resource(ResourceArn=arn3, Tags=[{"Key": "foo", "Value": "1"}])

        assert len(sns_client1.list_tags_for_resource(ResourceArn=arn1)["Tags"]) == 1
        assert len(sns_client2.list_tags_for_resource(ResourceArn=arn2)["Tags"]) == 2
        assert len(sns_client2.list_tags_for_resource(ResourceArn=arn3)["Tags"]) == 1