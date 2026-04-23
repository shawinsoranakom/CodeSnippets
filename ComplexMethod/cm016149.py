def get_artifacts_urls(results, suites, is_rocm=False):
    urls = {}
    # Sort by time (oldest first) to prefer earlier completed workflow runs
    # over potentially still-running newer ones
    sorted_results = sorted(results, key=lambda x: x.get("time", ""))
    for r in sorted_results:
        if (
            r["workflowName"] in ("inductor", "inductor-periodic")
            and "test" in r["jobName"]
            and "build" not in r["jobName"]
            and "runner-determinator" not in r["jobName"]
            and "unit-test" not in r["jobName"]
        ):
            # Filter out CUDA-13 jobs so it won't override CUDA-12 results.
            # The result files should be shared between CUDA-12 and CUDA-13, but
            # CUDA-13 skips more tests at the moment.
            if "cuda13" in r["jobName"]:
                continue

            # Filter based on whether this is a ROCm or CUDA job
            job_is_rocm = "rocm" in r["jobName"].lower()
            if job_is_rocm != is_rocm:
                continue

            *_, test_str = parse_job_name(r["jobName"])
            suite, shard_id, num_shards, machine, *_ = parse_test_str(test_str)
            workflowId = r["workflowId"]
            id = r["id"]
            runAttempt = r["runAttempt"]

            if suite in suites:
                artifact_filename = f"test-reports-test-{suite}-{shard_id}-{num_shards}-{machine}_{id}.zip"
                s3_url = f"{S3_BASE_URL}/{repo}/{workflowId}/{runAttempt}/artifact/{artifact_filename}"
                # Collect all candidate URLs per (suite, shard), ordered oldest first
                key = (suite, int(shard_id))
                if key not in urls:
                    urls[key] = []
                if s3_url not in urls[key]:
                    urls[key].append(s3_url)
    return urls