def send_metric_report(metric_path: str, source_type: str, timestamp: str):
    """

    SCHEMA >
    `timestamp` DateTime `json:$.timestamp`,
    `ls_source` String `json:$.ls_source`,
    `test_node_id` String `json:$.test_node_id`,
    `operation` String `json:$.operation`,
    `origin` String `json:$.origin`,
    `parameters` String `json:$.parameters`,
    `response_code` String `json:$.response_code`,
    `service` String `json:$.service`,
    `snapshot` UInt8 `json:$.snapshot`,
    `snapshot_skipped_paths` String `json:$.snapshot_skipped_paths`,
    `aws_validated` UInt8 `json:$.aws_validated`,
    `xfail` UInt8 `json:$.xfail`,
    `build_id` String `json:$.build_id`
    """
    tmp: list[str] = []
    count: int = 0
    build_id = os.environ.get("CIRCLE_WORKFLOW_ID", "") or os.environ.get("GITHUB_RUN_ID", "")
    send_metadata_for_build(build_id, timestamp)

    pathlist = Path(metric_path).rglob("metric-report-raw-data-*.csv")
    for path in pathlist:
        print(f"checking {str(path)}")
        with open(path) as csv_obj:
            reader_obj = csv.DictReader(csv_obj)
            data_to_remove = [field for field in reader_obj.fieldnames if field not in DATA_TO_KEEP]
            for row in reader_obj:
                count = count + 1

                # add timestamp, build_id, ls_source
                row["timestamp"] = timestamp
                row["build_id"] = build_id
                row["ls_source"] = source_type

                # remove data we are currently not interested in
                for field in data_to_remove:
                    row.pop(field, None)

                # convert boolean values
                for convert in CONVERT_TO_BOOL:
                    row[convert] = convert_to_bool(row[convert])

                tmp.append(json.dumps(row))
                if len(tmp) == 500:
                    # send data in batches
                    send_data_to_tinybird(tmp, data_name=DATA_SOURCE_RAW_TESTS)
                    tmp.clear()

        if tmp:
            # send last batch
            send_data_to_tinybird(tmp, data_name=DATA_SOURCE_RAW_TESTS)
            tmp.clear()

    print(f"---> processed {count} rows from community test coverage {metric_path}")