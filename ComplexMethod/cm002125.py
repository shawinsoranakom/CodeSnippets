def create_circleci_config(folder=None):
    if folder is None:
        folder = os.getcwd()
    os.environ["test_preparation_dir"] = folder
    jobs = [k for k in ALL_TESTS if os.path.isfile(os.path.join("test_preparation", f"{k.job_name}_test_list.txt"))]
    print("The following jobs will be run ", jobs)

    if len(jobs) == 0:
        jobs = [EmptyJob()]
    else:
        print(
            "Full list of job name inputs",
            {j.job_name + "_test_list": {"type": "string", "default": ""} for j in jobs},
        )
        # Add a job waiting all the test jobs and aggregate their test summary files at the end
        collection_job = EmptyJob()
        collection_job.job_name = "collection_job"
        jobs = [collection_job] + jobs

    config = {
        "version": "2.1",
        "parameters": {
            # Only used to accept the parameters from the trigger
            "nightly": {"type": "boolean", "default": False},
            # Only used to accept the parameters from GitHub Actions trigger
            "GHA_Actor": {"type": "string", "default": ""},
            "GHA_Action": {"type": "string", "default": ""},
            "GHA_Event": {"type": "string", "default": ""},
            "GHA_Meta": {"type": "string", "default": ""},
            "tests_to_run": {"type": "string", "default": ""},
            **{j.job_name + "_test_list": {"type": "string", "default": ""} for j in jobs},
            **{j.job_name + "_parallelism": {"type": "integer", "default": 1} for j in jobs},
        },
        "jobs": {j.job_name: j.to_dict() for j in jobs},
    }
    if "CIRCLE_TOKEN" in os.environ:
        # For private forked repo. (e.g. new model addition)
        config["workflows"] = {
            "version": 2,
            "run_tests": {"jobs": [{j.job_name: {"context": ["TRANSFORMERS_CONTEXT"]}} for j in jobs]},
        }
    else:
        # For public repo. (e.g. `transformers`)
        config["workflows"] = {"version": 2, "run_tests": {"jobs": [j.job_name for j in jobs]}}
    with open(os.path.join(folder, "generated_config.yml"), "w", encoding="utf-8") as f:
        f.write(
            yaml.dump(config, sort_keys=False, default_flow_style=False)
            .replace("' << pipeline", " << pipeline")
            .replace(">> '", " >>")
        )