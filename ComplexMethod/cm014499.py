def add_conclusions(edges: Any) -> None:
        for edge_idx, edge in enumerate(edges):
            node = edge["node"]
            workflow_run = node["workflowRun"]
            checkruns = node["checkRuns"]

            workflow_obj: WorkflowCheckState = no_workflow_obj

            if workflow_run is not None:
                # This is the usual workflow run ID we see on GitHub
                workflow_run_id = workflow_run["databaseId"]
                # While this is the metadata name and ID of the workflow itself
                workflow_name = workflow_run["workflow"]["name"]
                workflow_id = workflow_run["workflow"]["databaseId"]

                workflow_conclusion = node["conclusion"]
                # Do not override existing status with cancelled
                if workflow_conclusion == "CANCELLED" and workflow_name in workflows:
                    continue

                # Only keep the latest workflow run for each workflow, heuristically,
                # it's the run with largest run ID
                if (
                    workflow_id not in workflows
                    or workflows[workflow_id].run_id < workflow_run_id
                ):
                    workflows[workflow_id] = WorkflowCheckState(
                        name=workflow_name,
                        status=workflow_conclusion,
                        url=workflow_run["url"],
                        run_id=workflow_run_id,
                    )
                workflow_obj = workflows[workflow_id]

            while checkruns is not None:
                for checkrun_node in checkruns["nodes"]:
                    if not isinstance(checkrun_node, dict):
                        warn(f"Expected dictionary, but got {type(checkrun_node)}")
                        continue
                    checkrun_name = f"{get_check_run_name_prefix(workflow_run)}{checkrun_node['name']}"
                    existing_checkrun = workflow_obj.jobs.get(checkrun_name)
                    if existing_checkrun is None or not is_passing_status(
                        existing_checkrun.status
                    ):
                        workflow_obj.jobs[checkrun_name] = JobCheckState(
                            checkrun_name,
                            checkrun_node["detailsUrl"],
                            checkrun_node["conclusion"],
                            classification=None,
                            job_id=checkrun_node["databaseId"],
                            title=checkrun_node["title"],
                            summary=checkrun_node["summary"],
                        )

                if bool(checkruns["pageInfo"]["hasNextPage"]):
                    checkruns = get_next_checkruns_page(edges, edge_idx, checkruns)
                else:
                    checkruns = None