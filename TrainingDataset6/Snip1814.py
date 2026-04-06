def _skip_old_lines(log_file):
    size = os.path.getsize(os.environ['THEFUCK_OUTPUT_LOG'])
    if size > const.LOG_SIZE_IN_BYTES:
        log_file.seek(size - const.LOG_SIZE_IN_BYTES)