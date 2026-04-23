def main() -> None:
    args = parse_args()
    # Load the original test matrix set by the workflow. Its format, however,
    # doesn't follow the strict JSON format, so we load it using yaml here for
    # its more relaxed syntax
    test_matrix = yaml.safe_load(args.test_matrix)

    if test_matrix is None:
        warnings.warn(f"Invalid test matrix input '{args.test_matrix}', exiting")
        # We handle invalid test matrix gracefully by marking it as empty
        set_output("is-test-matrix-empty", True)
        sys.exit(0)

    pr_number = args.pr_number
    tag = args.tag

    # If the tag matches, we can get the PR number from it, this is from ciflow
    # workflow dispatcher
    tag_regex = re.compile(r"^ciflow/[\w\-]+/(?P<pr_number>\d+)$")

    labels = set()
    if pr_number:
        # If a PR number is set, query all the labels from that PR
        labels = get_labels(int(pr_number))
        # Then filter the test matrix and keep only the selected ones
        filtered_test_matrix = filter(test_matrix, labels)

    elif tag:
        m = tag_regex.match(tag)

        if m:
            pr_number = m.group("pr_number")

            # The PR number can also come from the tag in ciflow tag event
            labels = get_labels(int(pr_number))
            # Filter the test matrix and keep only the selected ones
            filtered_test_matrix = filter(test_matrix, labels)

        else:
            # There is a tag but it isn't ciflow, so there is nothing left to do
            filtered_test_matrix = test_matrix

    else:
        # No PR number, no tag, we can just return the test matrix as it is
        filtered_test_matrix = test_matrix

    if args.selected_test_configs:
        selected_test_configs = {
            v.strip().lower()
            for v in args.selected_test_configs.split(",")
            if v.strip()
        }
        filtered_test_matrix = filter_selected_test_configs(
            filtered_test_matrix, selected_test_configs
        )

    if args.event_name == "schedule" and args.schedule == "29 8 * * *":
        # we don't want to run the mem leak check or disabled tests on normal
        # periodically scheduled jobs, only the ones at this time
        filtered_test_matrix = set_periodic_modes(filtered_test_matrix, args.job_name)

    if args.workflow and args.job_name and args.branch not in EXCLUDED_BRANCHES:
        # If both workflow and job name are available, we will check if the current job
        # is disabled and remove it and all its dependants from the test matrix
        filtered_test_matrix = remove_disabled_jobs(
            args.workflow, args.job_name, filtered_test_matrix
        )

        filtered_test_matrix = mark_unstable_jobs(
            args.workflow, args.job_name, filtered_test_matrix
        )

    pr_body = get_pr_info(int(pr_number)).get("body", "") if pr_number else ""

    perform_misc_tasks(
        labels=labels,
        test_matrix=filtered_test_matrix,
        job_name=args.job_name,
        pr_body=pr_body if pr_body else "",
        branch=args.branch,
        tag=tag,
    )

    # Set the filtered test matrix as the output
    set_output("test-matrix", json.dumps(filtered_test_matrix))

    filtered_test_matrix_len = len(filtered_test_matrix.get("include", []))
    # and also put a flag if the test matrix is empty, so subsequent jobs can
    # quickly check it without the need to parse the JSON string
    set_output("is-test-matrix-empty", filtered_test_matrix_len == 0)

    # Save the labels from the PR, so that we can use it later
    set_output("labels", json.dumps(list(labels)))