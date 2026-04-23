def create_delivery_stream(
        self,
        context: RequestContext,
        delivery_stream_name: DeliveryStreamName,
        delivery_stream_type: DeliveryStreamType = None,
        direct_put_source_configuration: DirectPutSourceConfiguration = None,
        kinesis_stream_source_configuration: KinesisStreamSourceConfiguration = None,
        delivery_stream_encryption_configuration_input: DeliveryStreamEncryptionConfigurationInput = None,
        s3_destination_configuration: S3DestinationConfiguration = None,
        extended_s3_destination_configuration: ExtendedS3DestinationConfiguration = None,
        redshift_destination_configuration: RedshiftDestinationConfiguration = None,
        elasticsearch_destination_configuration: ElasticsearchDestinationConfiguration = None,
        amazonopensearchservice_destination_configuration: AmazonopensearchserviceDestinationConfiguration = None,
        splunk_destination_configuration: SplunkDestinationConfiguration = None,
        http_endpoint_destination_configuration: HttpEndpointDestinationConfiguration = None,
        tags: TagDeliveryStreamInputTagList = None,
        amazon_open_search_serverless_destination_configuration: AmazonOpenSearchServerlessDestinationConfiguration = None,
        msk_source_configuration: MSKSourceConfiguration = None,
        snowflake_destination_configuration: SnowflakeDestinationConfiguration = None,
        iceberg_destination_configuration: IcebergDestinationConfiguration = None,
        database_source_configuration: DatabaseSourceConfiguration = None,
        **kwargs,
    ) -> CreateDeliveryStreamOutput:
        # TODO add support for database_source_configuration and direct_put_source_configuration
        store = self.get_store(context.account_id, context.region)
        delivery_stream_type = delivery_stream_type or DeliveryStreamType.DirectPut

        delivery_stream_arn = firehose_stream_arn(
            stream_name=delivery_stream_name,
            account_id=context.account_id,
            region_name=context.region,
        )

        if delivery_stream_name in store.delivery_streams.keys():
            raise ResourceInUseException(
                f"Firehose {delivery_stream_name} under accountId {context.account_id} already exists"
            )

        destinations: DestinationDescriptionList = []
        if elasticsearch_destination_configuration:
            destinations.append(
                DestinationDescription(
                    DestinationId=short_uid(),
                    ElasticsearchDestinationDescription=convert_es_config_to_desc(
                        elasticsearch_destination_configuration
                    ),
                )
            )
        if amazonopensearchservice_destination_configuration:
            db_description = convert_opensearch_config_to_desc(
                amazonopensearchservice_destination_configuration
            )
            destinations.append(
                DestinationDescription(
                    DestinationId=short_uid(),
                    AmazonopensearchserviceDestinationDescription=db_description,
                )
            )
        if s3_destination_configuration or extended_s3_destination_configuration:
            destinations.append(
                DestinationDescription(
                    DestinationId=short_uid(),
                    S3DestinationDescription=convert_s3_config_to_desc(
                        s3_destination_configuration
                    ),
                    ExtendedS3DestinationDescription=convert_extended_s3_config_to_desc(
                        extended_s3_destination_configuration
                    ),
                )
            )
        if http_endpoint_destination_configuration:
            destinations.append(
                DestinationDescription(
                    DestinationId=short_uid(),
                    HttpEndpointDestinationDescription=convert_http_config_to_desc(
                        http_endpoint_destination_configuration
                    ),
                )
            )
        if splunk_destination_configuration:
            LOG.warning(
                "Delivery stream contains a splunk destination (which is currently not supported)."
            )
        if redshift_destination_configuration:
            destinations.append(
                DestinationDescription(
                    DestinationId=short_uid(),
                    RedshiftDestinationDescription=convert_redshift_config_to_desc(
                        redshift_destination_configuration
                    ),
                )
            )
        if amazon_open_search_serverless_destination_configuration:
            LOG.warning(
                "Delivery stream contains a opensearch serverless destination (which is currently not supported)."
            )

        stream = DeliveryStreamDescription(
            DeliveryStreamName=delivery_stream_name,
            DeliveryStreamARN=delivery_stream_arn,
            DeliveryStreamStatus=DeliveryStreamStatus.ACTIVE,
            DeliveryStreamType=delivery_stream_type,
            HasMoreDestinations=False,
            VersionId="1",
            CreateTimestamp=datetime.now(),
            Destinations=destinations,
            Source=convert_source_config_to_desc(kinesis_stream_source_configuration),
        )
        delivery_stream_arn = stream["DeliveryStreamARN"]

        if delivery_stream_type == DeliveryStreamType.KinesisStreamAsSource:
            if not kinesis_stream_source_configuration:
                raise InvalidArgumentException("Missing delivery stream configuration")
            kinesis_stream_arn = kinesis_stream_source_configuration["KinesisStreamARN"]
            kinesis_stream_name = kinesis_stream_arn.split(":stream/")[1]

            def _startup():
                stream["DeliveryStreamStatus"] = DeliveryStreamStatus.CREATING
                try:
                    listener_function = functools.partial(
                        self._process_records,
                        context.account_id,
                        context.region,
                        delivery_stream_name,
                    )
                    process = kinesis_connector.listen_to_kinesis(
                        stream_name=kinesis_stream_name,
                        account_id=context.account_id,
                        region_name=context.region,
                        listener_func=listener_function,
                        wait_until_started=True,
                        ddb_lease_table_suffix=f"-firehose-{delivery_stream_name}",
                    )

                    self.kinesis_listeners[delivery_stream_arn] = process
                    stream["DeliveryStreamStatus"] = DeliveryStreamStatus.ACTIVE
                except Exception as e:
                    LOG.warning(
                        "Unable to create Firehose delivery stream %s: %s",
                        delivery_stream_name,
                        e,
                    )
                    stream["DeliveryStreamStatus"] = DeliveryStreamStatus.CREATING_FAILED

            run_for_max_seconds(25, _startup)

        if tags:
            tag_map = tag_list_to_map(tags)
            store.tags.update_tags(delivery_stream_arn, tag_map)
        store.delivery_streams[delivery_stream_name] = stream

        return CreateDeliveryStreamOutput(DeliveryStreamARN=stream["DeliveryStreamARN"])