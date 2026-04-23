def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--host')
    parser.add_argument('--list', action='store_true')

    args = parser.parse_args()
    host: str | None = args.host

    if os.environ.get("INVENTORY_EMIT_STDERR"):
        print('this is stderr', file=sys.stderr, end='')

    if host:
        outputs = host_outputs
    else:
        outputs = normal_outputs

    if not (output := outputs.get(os.environ.get('INVENTORY_TEST_MODE'))):
        print(f"The `INVENTORY_TEST_MODE` envvar should be one of: \n{os.linesep.join(outputs)}", file=sys.stderr)
        sys.exit(1)

    if callable(output):
        output()

    if host:
        output = output.get(host)

    if isinstance(output, bytes):
        sys.stdout.buffer.write(output)
    else:
        if not isinstance(output, str):
            output = json.dumps(output)

        print(output)