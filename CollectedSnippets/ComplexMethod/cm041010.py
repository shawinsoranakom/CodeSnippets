def _put_records(
        self,
        account_id: str,
        region_name: str,
        delivery_stream_name: str,
        unprocessed_records: list[Record],
    ) -> list[PutRecordBatchResponseEntry]:
        """Put a list of records to the firehose stream - either directly from a PutRecord API call, or
        received from an underlying Kinesis stream (if 'KinesisStreamAsSource' is configured)"""
        store = self.get_store(account_id, region_name)
        delivery_stream_description = store.delivery_streams.get(delivery_stream_name)
        if not delivery_stream_description:
            raise ResourceNotFoundException(
                f"Firehose {delivery_stream_name} under account {account_id} not found."
            )

        # preprocess records, add any missing attributes
        self._add_missing_record_attributes(unprocessed_records)

        for destination in delivery_stream_description.get("Destinations", []):
            # apply processing steps to incoming items
            proc_config = {}
            for child in destination.values():
                proc_config = (
                    isinstance(child, dict) and child.get("ProcessingConfiguration") or proc_config
                )
            records = list(unprocessed_records)
            if proc_config.get("Enabled") is not False:
                for processor in proc_config.get("Processors", []):
                    # TODO: run processors asynchronously, to avoid request timeouts on PutRecord API calls
                    records = self._preprocess_records(processor, records)

            if "ElasticsearchDestinationDescription" in destination:
                self._put_to_search_db(
                    "ElasticSearch",
                    destination["ElasticsearchDestinationDescription"],
                    delivery_stream_name,
                    records,
                    unprocessed_records,
                    region_name,
                )
            if "AmazonopensearchserviceDestinationDescription" in destination:
                self._put_to_search_db(
                    "OpenSearch",
                    destination["AmazonopensearchserviceDestinationDescription"],
                    delivery_stream_name,
                    records,
                    unprocessed_records,
                    region_name,
                )
            if "S3DestinationDescription" in destination:
                s3_dest_desc = (
                    destination["S3DestinationDescription"]
                    or destination["ExtendedS3DestinationDescription"]
                )
                self._put_records_to_s3_bucket(delivery_stream_name, records, s3_dest_desc)
            if "HttpEndpointDestinationDescription" in destination:
                http_dest = destination["HttpEndpointDestinationDescription"]
                end_point = http_dest["EndpointConfiguration"]
                url = end_point["Url"]
                record_to_send = {
                    "requestId": str(uuid.uuid4()),
                    "timestamp": (int(time.time())),
                    "records": [],
                }
                for record in records:
                    data = record.get("Data") or record.get("data")
                    record_to_send["records"].append({"data": to_str(data)})
                headers = {
                    "Content-Type": "application/json",
                }
                try:
                    requests.post(url, json=record_to_send, headers=headers)
                except Exception as e:
                    LOG.error(
                        "Unable to put Firehose records to HTTP endpoint %s.",
                        url,
                        exc_info=LOG.isEnabledFor(logging.DEBUG),
                    )
                    raise e
            if "RedshiftDestinationDescription" in destination:
                s3_dest_desc = destination["RedshiftDestinationDescription"][
                    "S3DestinationDescription"
                ]
                self._put_records_to_s3_bucket(delivery_stream_name, records, s3_dest_desc)

                redshift_dest_desc = destination["RedshiftDestinationDescription"]
                self._put_to_redshift(records, redshift_dest_desc)
        return [
            PutRecordBatchResponseEntry(RecordId=str(uuid.uuid4())) for _ in unprocessed_records
        ]