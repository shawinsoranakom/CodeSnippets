def test_create_clusters(self, aws_client):
        # create
        cluster_id = f"c-{short_uid()}"
        response = aws_client.redshift.create_cluster(
            ClusterIdentifier=cluster_id,
            NodeType="ra3.xlplus",
            MasterUsername="test",
            MasterUserPassword="testABc123",
            NumberOfNodes=2,
            PubliclyAccessible=False,
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

        # describe
        clusters = aws_client.redshift.describe_clusters()["Clusters"]
        matching = [c for c in clusters if c["ClusterIdentifier"] == cluster_id]
        assert matching

        # wait until available
        def check_running():
            result = aws_client.redshift.describe_clusters()["Clusters"]
            status = result[0].get("ClusterStatus")
            assert status == "available"
            return result[0]

        retries = 500 if is_aws_cloud() else 60
        sleep = 30 if is_aws_cloud() else 1
        retry(check_running, sleep=sleep, retries=retries)

        # delete
        response = aws_client.redshift.delete_cluster(
            ClusterIdentifier=cluster_id, SkipFinalClusterSnapshot=True
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

        # assert that cluster deleted
        def check_deleted():
            with pytest.raises(Exception) as e:
                aws_client.redshift.describe_clusters(ClusterIdentifier=cluster_id)
            assert "ClusterNotFound" in str(e)

        retry(check_deleted, sleep=sleep, retries=retries)