def store_cloudwatch_logs(
    logs_client,
    log_group_name,
    log_stream_name,
    log_output,
    start_time=None,
    auto_create_group: bool | None = True,
):
    if not is_api_enabled("logs"):
        return
    start_time = start_time or int(time.time() * 1000)
    log_output = to_str(log_output)

    if auto_create_group:
        # make sure that the log group exists, create it if not
        try:
            logs_client.create_log_group(logGroupName=log_group_name)
        except Exception as e:
            if "ResourceAlreadyExistsException" in str(e):
                # the log group already exists, this is fine
                pass
            else:
                raise e

    # create a new log stream for this lambda invocation
    try:
        logs_client.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)
    except Exception:  # TODO: narrow down
        pass

    # store new log events under the log stream
    finish_time = int(time.time() * 1000)
    # fix for log lines that were merged into a singe line, e.g., "log line 1 ... \x1b[32mEND RequestId ..."
    log_output = log_output.replace("\\x1b", "\n\\x1b")
    log_output = log_output.replace("\x1b", "\n\x1b")
    log_lines = log_output.split("\n")
    time_diff_per_line = float(finish_time - start_time) / float(len(log_lines))
    log_events = []
    for i, line in enumerate(log_lines):
        if not line:
            continue
        # simple heuristic: assume log lines were emitted in regular intervals
        log_time = start_time + float(i) * time_diff_per_line
        event = {"timestamp": int(log_time), "message": line}
        log_events.append(event)
    if not log_events:
        return
    logs_client.put_log_events(
        logGroupName=log_group_name, logStreamName=log_stream_name, logEvents=log_events
    )