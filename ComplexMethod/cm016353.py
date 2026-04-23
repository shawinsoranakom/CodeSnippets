def backfill_test_jsons_while_running(
    workflow_run_id: int, workflow_run_attempt: int
) -> None:
    # The bucket name name is a bit misleading, usually the jsons should be
    # uploaded while the job is running, but that won't happen if the job
    # doesn't have permissions to write to the bucket or if there was an error
    with TemporaryDirectory() as temp_dir:
        print("Using temporary directory:", temp_dir)
        os.chdir(temp_dir)

        # Download and extract all the reports (both GHA and S3)
        s3_xmls = download_s3_artifacts(
            "test-report", workflow_run_id, workflow_run_attempt
        )

        s3_jsons = download_s3_artifacts(
            "test-jsons", workflow_run_id, workflow_run_attempt
        )

        # Unzip artifacts and save their locations
        unzipped_xml_dirs = [unzip(path) for path in s3_xmls]
        unzipped_json_dirs = [unzip(path) for path in s3_jsons]

        all_existing_jsons = []
        for unzipped_dir in unzipped_json_dirs:
            all_existing_jsons.extend(
                [
                    str(Path(json_report).relative_to(unzipped_dir))
                    for json_report in unzipped_dir.glob("**/*.json")
                ]
            )

        for unzipped_dir in unzipped_xml_dirs:
            for xml in unzipped_dir.glob("**/*.xml"):
                corresponding_json = str(
                    xml.with_suffix(".json").relative_to(
                        unzipped_dir / "test" / "test-reports"
                    )
                )
                if corresponding_json in all_existing_jsons:
                    print(f"Skipping upload for existing test json for {xml}")
                    continue
                # print(f"Uploading missing test json for {xml}")
                job_id = get_job_id(xml)
                test_cases = parse_xml_report(
                    "testcase",
                    xml,
                    workflow_run_id,
                    workflow_run_attempt,
                    job_id,
                )
                json_file = xml.with_suffix(".json")
                s3_key = (
                    json_file.relative_to(unzipped_dir / "test" / "test-reports")
                    .as_posix()
                    .replace("/", "_")
                )
                s3_key = f"test_jsons_while_running/{workflow_run_id}/{job_id}/{s3_key}"
                upload_to_s3("gha-artifacts", s3_key, remove_nan_inf(test_cases))