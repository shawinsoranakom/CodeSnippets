def communicate_with_process(
    name: str,
    process: subprocess.Popen,
    stdin: t.Optional[bytes],
    stdout: bool,
    stderr: bool,
    capture: bool,
    output_stream: OutputStream,
) -> tuple[bytes, bytes]:
    """Communicate with the specified process, handling stdin/stdout/stderr as requested."""
    threads: list[WrappedThread] = []
    reader: t.Type[ReaderThread]

    if capture:
        reader = CaptureThread
    else:
        reader = OutputThread

    if stdin is not None:
        threads.append(WriterThread(process.stdin, stdin, name))

    if stdout:
        stdout_reader = reader(process.stdout, output_stream.get_buffer(sys.stdout.buffer), name)
        threads.append(stdout_reader)
    else:
        stdout_reader = None

    if stderr:
        stderr_reader = reader(process.stderr, output_stream.get_buffer(sys.stderr.buffer), name)
        threads.append(stderr_reader)
    else:
        stderr_reader = None

    for thread in threads:
        thread.start()

    for thread in threads:
        try:
            thread.wait_for_result()
        except Exception as ex:  # pylint: disable=broad-except
            display.error(str(ex))

    if isinstance(stdout_reader, ReaderThread):
        stdout_bytes = b''.join(stdout_reader.lines)
    else:
        stdout_bytes = b''

    if isinstance(stderr_reader, ReaderThread):
        stderr_bytes = b''.join(stderr_reader.lines)
    else:
        stderr_bytes = b''

    process.wait()

    return stdout_bytes, stderr_bytes