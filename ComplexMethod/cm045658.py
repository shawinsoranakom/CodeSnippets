def replay_csv_with_time(
    path: str,
    *,
    schema: type[pw.Schema],
    time_column: str,
    unit: str = "s",
    autocommit_ms: int = 100,
    speedup: float = 1,
) -> pw.Table:
    """
    Replay a static CSV files as a data stream while respecting the time between updated based on a timestamp columns.
    The timestamps in the file should be ordered positive integers.

    Args:
        path: Path to the file to stream.
        schema: Schema of the resulting table.
        time_column: Column containing the timestamps.
        unit: Unit of the timestamps. Only 's', 'ms', 'us', and 'ns' are supported. Defaults to 's'.
        autocommit_duration_ms: the maximum time between two commits. Every
          autocommit_duration_ms milliseconds, the updates received by the connector are
          committed and pushed into Pathway's computation graph.
        speedup: Produce stream `speedup` times faster than it would result from the time column.

    Returns:
        Table: The table read.

    Note: the CSV files should follow a standard CSV settings. The separator is ',', the
    quotechar is '"', and there is no escape.

    """

    time_column_type = schema.typehints().get(time_column, None)
    if time_column_type != int and time_column_type != float:
        raise ValueError("Invalid schema. Time columns must be int or float.")

    if unit not in ["s", "ms", "us", "ns"]:
        raise ValueError(
            "demo.replay_csv_with_time: unit should be either 's', 'ms, 'us', or 'ns'."
        )

    unit_factor = 1
    match unit:
        case "ms":
            unit_factor = 1000
        case "us":
            unit_factor = 1_000_000
        case "ns":
            unit_factor = 1_000_000_000
        case _:
            unit_factor = 1
    speedup *= unit_factor

    columns = set(schema.column_names())

    class FileStreamSubject(pw.io.python.ConnectorSubject):
        def run(self):
            with open(path, newline="") as csvfile:
                csvreader = csv.DictReader(csvfile)
                firstrow = next(iter(csvreader))
                values = {key: firstrow[key] for key in columns}
                first_time_value = float(values[time_column])
                real_start_time = datetime.now().timestamp()
                self.next_json(values)

                for row in csvreader:
                    values = {key: row[key] for key in columns}
                    current_value = float(values[time_column])
                    expected_time_from_start = current_value - first_time_value
                    expected_time_from_start /= speedup
                    real_time_from_start = datetime.now().timestamp() - real_start_time
                    tts = expected_time_from_start - real_time_from_start
                    if tts > 0:
                        time.sleep(tts)
                    self.next_json(values)

    return pw.io.python.read(
        FileStreamSubject(datasource_name="demo.replay-csv-with-time"),
        schema=schema.with_types(**{name: str for name in schema.column_names()}),
        autocommit_duration_ms=autocommit_ms,
        format="json",
    ).cast_to_types(**schema.typehints())