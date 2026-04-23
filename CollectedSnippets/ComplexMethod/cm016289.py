def check_file(filename: str) -> list[LintMessage]:
    logging.debug("Checking file %s", filename)

    workflow = load_yaml(Path(filename))
    bad_jobs: dict[str, str | None] = {}
    if type(workflow) is not dict:
        return []

    # yaml parses "on" as True
    triggers = workflow.get(True, {})
    triggers_to_check = ["push", "schedule", "pull_request", "pull_request_target"]
    if not any(trigger in triggers_to_check for trigger in triggers):
        return []

    jobs = workflow.get("jobs", {})
    for job, definition in jobs.items():
        if definition.get("needs"):
            # The parent job will have the if statement
            continue

        if_statement = definition.get("if")

        if if_statement is None:
            bad_jobs[job] = None
        elif type(if_statement) is bool and not if_statement:
            # if: false
            pass
        else:
            if_statement = str(if_statement)
            valid_checks: list[Callable[[str], bool]] = [
                lambda x: "github.repository == 'pytorch/pytorch'" in x
                and "github.event_name != 'schedule' || github.repository == 'pytorch/pytorch'"
                not in x,
                lambda x: "github.repository_owner == 'pytorch'" in x,
            ]
            if not any(f(if_statement) for f in valid_checks):
                bad_jobs[job] = if_statement

    with open(filename) as f:
        lines = f.readlines()

    smart_enough = True
    original = "".join(lines)
    iterator = iter(range(len(lines)))
    replacement = ""
    for i in iterator:
        line = lines[i]
        # Search for job name
        re_match = re.match(r"( +)([-_\w]*):", line)
        if not re_match or re_match.group(2) not in bad_jobs:
            replacement += line
            continue
        job_name = re_match.group(2)

        failure_type = bad_jobs[job_name]
        if failure_type is None:
            # Just need to add an if statement
            replacement += (
                f"{line}{re_match.group(1)}  if: github.repository_owner == 'pytorch'\n"
            )
            continue

        # Search for if statement
        while re.match(r"^ +if:", line) is None:
            replacement += line
            i = next(iterator)
            line = lines[i]
        if i + 1 < len(lines) and not re.match(r"^ +(.*):", lines[i + 1]):
            # This is a multi line if statement
            smart_enough = False
            break

        if_statement_match = re.match(r"^ +if: ([^#]*)(#.*)?$", line)
        # Get ... in if: ... # comments
        if not if_statement_match:
            return [
                gen_lint_message(
                    description=f"Something went wrong when looking at {job_name}.",
                )
            ]

        if_statement = if_statement_match.group(1).strip()

        # Handle comment in if: ... # comments
        comments = if_statement_match.group(2) or ""
        if comments:
            comments = " " + comments

        # Too broad of a check, but should catch everything
        needs_parens = "||" in if_statement

        # Handle ${{ ... }}
        has_brackets = re.match(r"\$\{\{(.*)\}\}", if_statement)
        internal_statement = (
            has_brackets.group(1).strip() if has_brackets else if_statement
        )

        if needs_parens:
            internal_statement = f"({internal_statement})"
        new_line = f"{internal_statement} && github.repository_owner == 'pytorch'"

        # I don't actually know if we need the ${{ }} but do it just in case
        new_line = "${{ " + new_line + " }}" + comments

        replacement += f"{re_match.group(1)}  if: {new_line}\n"

    description = (
        "Please add checks for if: github.repository_owner == 'pytorch' in the following jobs in this file: "
        + ", ".join(job for job in bad_jobs)
    )

    if not smart_enough:
        return [
            gen_lint_message(
                filename=filename,
                description=description,
            )
        ]

    if replacement == original:
        return []

    return [
        gen_lint_message(
            filename=filename,
            original=original,
            replacement=replacement,
            description=description,
        )
    ]