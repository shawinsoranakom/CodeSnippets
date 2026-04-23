def get_runner_prefix(
    rollout_state: str,
    workflow_requestors: Iterable[str],
    branch: str,
    eligible_experiments: frozenset[str] = frozenset(),
    opt_out_experiments: frozenset[str] = frozenset(),
    is_canary: bool = False,
) -> RunnerPrefixResult:
    settings = parse_settings(rollout_state)
    user_optins = parse_users(rollout_state)

    fleet_prefix = ""
    prefixes = []
    use_arc = False
    for experiment_name, experiment_settings in settings.experiments.items():
        if not experiment_settings.all_branches and is_exception_branch(branch):
            log.info(
                f"Branch {branch} is an exception branch. Not enabling experiment {experiment_name}."
            )
            continue

        if opt_out_experiments:
            if experiment_name in opt_out_experiments:
                opt_out_exp_list = ", ".join(opt_out_experiments)
                log.info(
                    f"Skipping experiment '{experiment_name}', as this workflow has opted-out (opted out experiments are: {opt_out_exp_list})"
                )
                continue

        if eligible_experiments:
            if experiment_name not in eligible_experiments:
                exp_list = ", ".join(eligible_experiments)
                log.info(
                    f"Skipping experiment '{experiment_name}', as it is not in the eligible_experiments list: {exp_list}"
                )
                continue
        elif not experiment_settings.default:
            log.info(
                f"Skipping experiment '{experiment_name}', as it is not a default experiment"
            )
            continue

        # Is any workflow_requestor opted out to this experiment?
        opted_out_users = [
            requestor
            for requestor in workflow_requestors
            if is_user_opted_out(requestor, user_optins, experiment_name)
        ]

        if opted_out_users:
            log.info(
                f"{', '.join(opted_out_users)} have opted out of experiment {experiment_name}."
            )
            continue

        # Is any workflow_requestor opted in to this experiment?
        opted_in_users = [
            requestor
            for requestor in workflow_requestors
            if is_user_opted_in(requestor, user_optins, experiment_name)
        ]

        enabled = False
        if opted_in_users:
            # Get the minimum per-user rollout percentage among opted-in requesters.
            # This is conservative: if the PR author sets 10%, that intent is respected
            # even if the triggering actor (e.g. pytorchmergebot) has 100%.
            user_rollout_percs = [
                get_user_experiment_config(u, user_optins, experiment_name).rollout_perc
                for u in opted_in_users
            ]
            min_perc = min(user_rollout_percs)

            if min_perc >= 100:
                log.info(
                    f"{', '.join(opted_in_users)} have opted into experiment {experiment_name}."
                )
                enabled = True
            elif min_perc > 0:
                if random.uniform(0, 100) <= min_perc:
                    log.info(
                        f"{', '.join(opted_in_users)} have opted into experiment {experiment_name} "
                        f"with {min_perc}% rollout. Enabling this run."
                    )
                    enabled = True
                else:
                    log.info(
                        f"{', '.join(opted_in_users)} have opted into experiment {experiment_name} "
                        f"with {min_perc}% rollout. Not enabling this run."
                    )
            else:
                log.info(
                    f"{', '.join(opted_in_users)} have opted into experiment {experiment_name} "
                    f"with 0% rollout. Not enabling."
                )

        elif experiment_settings.rollout_perc:
            # If no user is opted in, then we randomly enable the experiment based on the rollout percentage
            if random.uniform(0, 100) <= experiment_settings.rollout_perc:
                log.info(
                    f"Based on rollout percentage of {experiment_settings.rollout_perc}%, enabling experiment {experiment_name}."
                )
                enabled = True

        if enabled:
            label = experiment_name
            if experiment_name == ARC_FLEET_EXPERIMENT:
                use_arc = True
                log.info(
                    f"ARC experiment enabled. Using ARC runner prefix ({'canary' if is_canary else 'production'})."
                )
            elif experiment_name == LF_FLEET_EXPERIMENT:
                # We give some special treatment to the "lf" experiment since determines the fleet we use
                #  - If it's enabled, then we always list it's prefix first
                #  - If we're in the canary branch, then we append ".c" to the lf prefix
                if is_canary:
                    label += CANARY_FLEET_SUFFIX
                fleet_prefix = label
            else:
                prefixes.append(label)

    # ARC experiment takes precedence: return a fixed label prefix
    if use_arc:
        arc_prefix = (
            ARC_CANARY_LABEL_PREFIX + ARC_LABEL_PREFIX
            if is_canary
            else ARC_LABEL_PREFIX
        )
        return RunnerPrefixResult(prefix=arc_prefix, use_arc=True)

    if len(prefixes) > 1:
        log.error(
            f"Only a fleet and one other experiment can be enabled for a job at any time. Enabling {prefixes[0]} and ignoring the rest, which are {', '.join(prefixes[1:])}"
        )
        prefixes = prefixes[:1]

    # Fleet always comes first
    if fleet_prefix:
        prefixes.insert(0, fleet_prefix)

    prefix = ".".join(prefixes) + "." if prefixes else ""
    return RunnerPrefixResult(prefix=prefix)