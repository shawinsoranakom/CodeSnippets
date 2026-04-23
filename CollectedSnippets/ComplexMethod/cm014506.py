def parse_user_opt_in_from_text(user_optin_text: str) -> UserOptins:
    """
    Parse the user opt-in text into a key value pair of username and the list of features they have opted into

    Users are GitHub usernames with the @ prefix. Each user is also a comma-separated list of features/experiments to enable.
        - Example line: "@User1,lf,split_build"
        - A "#" prefix indicates the user is opted out of all experiments


    """
    optins = UserOptins()
    for user in user_optin_text.split("\n"):
        user = user.strip("\r\n\t -")
        if not user or not user.startswith("@"):
            # Not a valid user. Skip
            continue

        if user:
            usr_name = user.split(",")[0].strip("@")
            configs = []
            for exp_str in user.split(",")[1:]:
                exp_str = exp_str.strip(" ")
                if not exp_str:
                    continue
                # Parse optional per-user rollout percentage (e.g. "arc:10")
                # Opt-out entries (e.g. "-lf") never have a percentage
                if ":" in exp_str and not exp_str.startswith("-"):
                    name, perc_str = exp_str.split(":", 1)
                    try:
                        perc = float(perc_str)
                    except ValueError:
                        log.warning(
                            f"Invalid rollout percentage for user {usr_name}, experiment {exp_str}. Defaulting to 100%."
                        )
                        perc = 100
                    if not (0 <= perc <= 100):
                        log.warning(
                            f"Rollout percentage {perc} for user {usr_name}, experiment {name} "
                            f"is out of range [0, 100]. Clamping."
                        )
                        perc = max(0.0, min(100.0, perc))
                    configs.append(UserExperimentConfig(name=name, rollout_perc=perc))
                else:
                    configs.append(UserExperimentConfig(name=exp_str, rollout_perc=100))
            optins[usr_name] = configs

    return optins