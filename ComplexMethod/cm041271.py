def get_lambda_log_events(
    function_name,
    delay_time=DEFAULT_GET_LOG_EVENTS_DELAY,
    regex_filter: str | None = None,
    log_group=None,
    logs_client=None,
):
    def get_log_events(func_name, delay):
        time.sleep(delay)
        log_group_name = log_group or get_lambda_log_group_name(func_name)
        return list_all_log_events(log_group_name, logs_client)

    try:
        events = get_log_events(function_name, delay_time)
    except Exception as e:
        if "ResourceNotFoundException" in str(e):
            return []
        raise

    rs = []
    for event in events:
        raw_message = event["message"]
        if (
            not raw_message
            or raw_message.startswith("INIT_START")
            or raw_message.startswith("START")
            or raw_message.startswith("END")
            or raw_message.startswith(
                "REPORT"
            )  # necessary until tail is updated in docker images. See this PR:
            # http://git.savannah.gnu.org/gitweb/?p=coreutils.git;a=commitdiff;h=v8.24-111-g1118f32
            or "tail: unrecognized file system type" in raw_message
            or regex_filter
            and not re.search(regex_filter, raw_message)
        ):
            continue
        if raw_message in ["\x1b[0m", "\\x1b[0m"]:
            continue

        try:
            rs.append(json.loads(raw_message))
        except Exception:
            rs.append(raw_message)

    return rs