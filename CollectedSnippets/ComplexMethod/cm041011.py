def _put_to_search_db(
        self,
        db_flavor,
        db_description,
        delivery_stream_name,
        records,
        unprocessed_records,
        region_name,
    ):
        """
        sends Firehose records to an ElasticSearch or Opensearch database
        """
        search_db_index = db_description["IndexName"]
        domain_arn = db_description.get("DomainARN")
        cluster_endpoint = db_description.get("ClusterEndpoint")
        if cluster_endpoint is None:
            cluster_endpoint = get_opensearch_endpoint(domain_arn)

        db_connection = get_search_db_connection(cluster_endpoint, region_name)

        if db_description.get("S3BackupMode") == ElasticsearchS3BackupMode.AllDocuments:
            s3_dest_desc = db_description.get("S3DestinationDescription")
            if s3_dest_desc:
                try:
                    self._put_records_to_s3_bucket(
                        stream_name=delivery_stream_name,
                        records=unprocessed_records,
                        s3_destination_description=s3_dest_desc,
                    )
                except Exception as e:
                    LOG.warning("Unable to backup unprocessed records to S3. Error: %s", e)
            else:
                LOG.warning("Passed S3BackupMode without S3Configuration. Cannot backup...")
        elif db_description.get("S3BackupMode") == ElasticsearchS3BackupMode.FailedDocumentsOnly:
            # TODO support FailedDocumentsOnly as well
            LOG.warning("S3BackupMode FailedDocumentsOnly is set but currently not supported.")
        for record in records:
            obj_id = uuid.uuid4()

            data = "{}"
            # DirectPut
            if "Data" in record:
                data = base64.b64decode(record["Data"])
            # KinesisAsSource
            elif "data" in record:
                data = base64.b64decode(record["data"])

            try:
                body = json.loads(data)
            except Exception as e:
                LOG.warning("%s only allows json input data!", db_flavor)
                raise e

            if LOG.isEnabledFor(logging.DEBUG):
                LOG.debug(
                    "Publishing to %s destination. Data: %s",
                    db_flavor,
                    truncate(data, max_length=300),
                )
            try:
                db_connection.create(index=search_db_index, id=obj_id, body=body)
            except Exception as e:
                LOG.error(
                    "Unable to put record to stream %s.",
                    delivery_stream_name,
                    exc_info=LOG.isEnabledFor(logging.DEBUG),
                )
                raise e