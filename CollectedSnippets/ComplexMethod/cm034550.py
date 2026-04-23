def get_coverage_runs():
    list_response = requests.get("https://dev.azure.com/ansible/ansible/_apis/pipelines/%s/runs?api-version=6.0-preview.1" % PIPELINE_ID)
    list_response.raise_for_status()

    runs = list_response.json()

    coverage_runs = []
    for run_summary in runs["value"][0:1000]:
        run_response = requests.get(run_summary['url'])

        if run_response.status_code == 500 and 'Cannot serialize type Microsoft.Azure.Pipelines.WebApi.ContainerResource' in run_response.json()['message']:
            # This run used a container resource, which AZP can no longer serialize for anonymous requests.
            # Assume all older requests have this issue as well and stop further processing of runs.
            # The issue was reported here: https://developercommunity.visualstudio.com/t/Pipelines-API-serialization-error-for-an/10294532
            # A work-around for this issue was applied in: https://github.com/ansible/ansible/pull/80299
            break

        run_response.raise_for_status()
        run = run_response.json()

        if run['resources']['repositories']['self']['refName'] != 'refs/heads/%s' % BRANCH:
            continue

        if 'finishedDate' in run_summary:
            age = datetime.datetime.now() - datetime.datetime.strptime(run['finishedDate'].split(".")[0], "%Y-%m-%dT%H:%M:%S")
            if age > MAX_AGE:
                break

        artifact_response = requests.get("https://dev.azure.com/ansible/ansible/_apis/build/builds/%s/artifacts?api-version=6.0" % run['id'])
        artifact_response.raise_for_status()

        artifacts = artifact_response.json()['value']
        if any(a["name"].startswith("Coverage") for a in artifacts):
            # TODO wrongfully skipped if all jobs failed.
            coverage_runs.append(run)

    return coverage_runs