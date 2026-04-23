def parse_xml_and_upload_json() -> None:
    """
    Parse xml test reports that do not yet have a corresponding json report
    uploaded to s3, and upload the json reports to s3. Use filelock to avoid
    uploading the same file from multiple processes.
    """
    try:
        job_id: int | None = int(os.environ.get("JOB_ID", 0))
        if job_id == 0:
            job_id = None
    except (ValueError, TypeError):
        job_id = None

    try:
        for xml_file in glob.glob(
            f"{REPO_ROOT}/test/test-reports/**/*.xml", recursive=True
        ):
            xml_path = Path(xml_file)
            json_file = xml_path.with_suffix(".json")
            lock = FileLock(str(json_file) + ".lock")

            try:
                lock.acquire(timeout=0)  # immediately fails if already locked
                if json_file.exists():
                    continue  # already uploaded
                test_cases = parse_xml_report(
                    "testcase",
                    xml_path,
                    int(os.environ.get("GITHUB_RUN_ID", "0")),
                    int(os.environ.get("GITHUB_RUN_ATTEMPT", "0")),
                    job_id,
                )
                line_by_line_jsons = "\n".join([json.dumps(tc) for tc in test_cases])

                gzipped = gzip.compress(line_by_line_jsons.encode("utf-8"))
                s3_key = (
                    json_file.relative_to(REPO_ROOT / "test/test-reports")
                    .as_posix()
                    .replace("/", "_")
                )

                get_s3_resource().put_object(
                    Body=gzipped,
                    Bucket="gha-artifacts",
                    Key=f"test_jsons_while_running/{os.environ.get('GITHUB_RUN_ID')}/{job_id}/{s3_key}",
                    ContentType="application/json",
                    ContentEncoding="gzip",
                )

                # We don't need to save the json file locally, but doing so lets us
                # track which ones have been uploaded already. We could probably also
                # check S3
                with open(json_file, "w") as f:
                    f.write(line_by_line_jsons)
            except Timeout:
                continue  # another process is working on this file
            finally:
                if lock.is_locked:
                    lock.release()
    except Exception as e:
        print(f"Failed to parse and upload json test reports: {e}")