def test_postgres_read_and_parse_extra_types(tmp_path, postgres):
    class InputSchema(pw.Schema):
        id: str = pw.column_definition(primary_key=True)
        birthday: pw.DateTimeNaive
        meeting_time: pw.Duration
        meeting_timetz: pw.Duration
        ip_addr: str
        network: str
        mac_addr: str
        object_id: int
        price: float
        value: str

    output_path = tmp_path / "output.jsonl"
    table_name = postgres.random_table_name()

    postgres.execute_sql(
        f"""
        CREATE TABLE {table_name} (
            id UUID PRIMARY KEY,
            birthday DATE NOT NULL,
            meeting_time TIME NOT NULL,
            meeting_timetz TIMETZ NOT NULL,
            ip_addr INET NOT NULL,
            network CIDR NOT NULL,
            mac_addr MACADDR NOT NULL,
            object_id OID NOT NULL,
            price NUMERIC(10, 4) NOT NULL,
            value TEXT NOT NULL
        );
        """
    )

    # Each row tests a different edge case combination
    rows_data = [
        # (id, birthday, meeting_time, meeting_timetz, ip_addr, network,
        # mac_addr, object_id, price, value, description)
        (
            "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
            "2025-03-14",
            "12:30:00",
            "12:30:00+02:00",  # positive timezone +02:00
            "192.168.1.1",  # IPv4 private
            "192.168.1.0/24",  # IPv4 CIDR
            "08:00:2b:01:02:03",
            12345,
            123.4567,
            "positive_tz",
        ),
        (
            "b1ffcd00-1d1c-5fa9-cc7e-7cc0ce491b22",
            "2025-03-14",
            "12:30:00",
            "12:30:00-05:00",  # negative timezone -05:00
            "10.0.0.1",  # IPv4 private class A
            "10.0.0.0/8",  # IPv4 CIDR /8
            "ff:ff:ff:ff:ff:ff",  # broadcast MAC
            99999,
            0.0001,  # very small price
            "negative_tz",
        ),
        (
            "c2ffcd00-1d1c-5fa9-cc7e-7cc0ce491b33",
            "2025-03-14",
            "00:00:00",  # midnight
            "00:00:00+00:00",  # UTC (zero offset)
            "2001:db8::1",  # IPv6 address
            "2001:db8::/32",  # IPv6 CIDR
            "00:00:00:00:00:00",  # zero MAC
            0,
            9999.9999,  # max price
            "ipv6_midnight_utc",
        ),
        (
            "d3ffcd00-1d1c-5fa9-cc7e-7cc0ce491b44",
            "1970-01-01",  # minimum DATE
            "23:59:59",  # end of day
            "23:59:59+14:00",  # maximum positive timezone +14:00
            "255.255.255.255",  # IPv4 broadcast
            "0.0.0.0/0",  # IPv4 default route
            "0a:0b:0c:0d:0e:0f",
            4294967295,  # max OID (2^32 - 1)
            1234.5678,
            "edge_max_tz",
        ),
        (
            "e4ffcd00-1d1c-5fa9-cc7e-7cc0ce491b55",
            "2099-12-31",  # maximum DATE
            "23:59:59",
            "23:59:59-12:00",  # minimum negative timezone -12:00
            "127.0.0.1",  # loopback IPv4
            "127.0.0.0/8",  # loopback CIDR
            "de:ad:be:ef:00:01",
            1,
            0.0000,  # zero price
            "edge_min_tz",
        ),
        (
            "f5ffcd00-1d1c-5fa9-cc7e-7cc0ce491b66",
            "2025-03-14",
            "12:30:00",
            "12:30:00+05:30",  # half-hour offset (India)
            "::1",  # IPv6 loopback
            "::1/128",  # IPv6 loopback CIDR /128
            "aa:bb:cc:dd:ee:ff",
            42,
            42.0000,
            "ipv6_loopback_half_tz",
        ),
    ]

    def _ns(h, m, s=0):
        """Convert hours/minutes/seconds to nanoseconds."""
        return (h * 3600 + m * 60 + s) * 1_000_000_000

    # Expected values per row value label
    expected = {
        "positive_tz": {
            "birthday": "2025-03-14T00:00:00.000000000",
            "meeting_time": _ns(12, 30),
            "meeting_timetz": _ns(10, 30),  # 12:30 - 02:00
            "ip_addr": "192.168.1.1",
            "network": "192.168.1.0/24",
            "mac_addr": "08:00:2b:01:02:03",
            "object_id": 12345,
            "price": 123.4567,
        },
        "negative_tz": {
            "birthday": "2025-03-14T00:00:00.000000000",
            "meeting_time": _ns(12, 30),
            "meeting_timetz": _ns(17, 30),  # 12:30 - (-05:00) = 17:30
            "ip_addr": "10.0.0.1",
            "network": "10.0.0.0/8",
            "mac_addr": "ff:ff:ff:ff:ff:ff",
            "object_id": 99999,
            "price": 0.0001,
        },
        "ipv6_midnight_utc": {
            "birthday": "2025-03-14T00:00:00.000000000",
            "meeting_time": _ns(0, 0),
            "meeting_timetz": _ns(0, 0),  # 00:00 UTC+00 → 00:00 UTC
            "ip_addr": "2001:db8::1",
            "network": "2001:db8::/32",
            "mac_addr": "00:00:00:00:00:00",
            "object_id": 0,
            "price": 9999.9999,
        },
        "edge_max_tz": {
            "birthday": "1970-01-01T00:00:00.000000000",
            "meeting_time": _ns(23, 59, 59),
            "meeting_timetz": _ns(9, 59, 59),  # 23:59:59 - 14:00 = 09:59:59
            "ip_addr": "255.255.255.255",
            "network": "0.0.0.0/0",
            "mac_addr": "0a:0b:0c:0d:0e:0f",
            "object_id": 4294967295,
            "price": 1234.5678,
        },
        "edge_min_tz": {
            "birthday": "2099-12-31T00:00:00.000000000",
            "meeting_time": _ns(23, 59, 59),
            "meeting_timetz": _ns(35, 59, 59),  # 23:59:59 - (-12:00) = 35:59:59
            "ip_addr": "127.0.0.1",
            "network": "127.0.0.0/8",
            "mac_addr": "de:ad:be:ef:00:01",
            "object_id": 1,
            "price": 0.0,
        },
        "ipv6_loopback_half_tz": {
            "birthday": "2025-03-14T00:00:00.000000000",
            "meeting_time": _ns(12, 30),
            "meeting_timetz": _ns(7, 0),  # 12:30 - 05:30 = 07:00
            "ip_addr": "::1",
            "network": "::1/128",
            "mac_addr": "aa:bb:cc:dd:ee:ff",
            "object_id": 42,
            "price": 42.0,
        },
    }

    # Insert snapshot rows (all except the last one which will be streamed)
    snapshot_rows = rows_data[:-1]
    streaming_row_data = rows_data[-1]

    for row in snapshot_rows:
        (rid, birthday, mtime, mtimetz, ip, net, mac, oid, price, val) = row
        postgres.execute_sql(
            f"""
            INSERT INTO {table_name}
            (id, birthday, meeting_time, meeting_timetz, ip_addr, network, mac_addr, object_id, price, value)
            VALUES (
                '{rid}', '{birthday}', '{mtime}', '{mtimetz}',
                '{ip}', '{net}', '{mac}', {oid}, {price}, '{val}'
            );
            """
        )

    def assert_row(row, value):
        exp = expected[value]
        assert row["birthday"] == exp["birthday"], f"[{value}] birthday mismatch"
        assert (
            row["meeting_time"] == exp["meeting_time"]
        ), f"[{value}] meeting_time mismatch"
        assert (
            row["meeting_timetz"] == exp["meeting_timetz"]
        ), f"[{value}] meeting_timetz mismatch"
        assert row["ip_addr"] == exp["ip_addr"], f"[{value}] ip_addr mismatch"
        assert row["network"] == exp["network"], f"[{value}] network mismatch"
        assert row["mac_addr"] == exp["mac_addr"], f"[{value}] mac_addr mismatch"
        assert row["object_id"] == exp["object_id"], f"[{value}] object_id mismatch"
        assert row["price"] == pytest.approx(
            exp["price"], rel=1e-4
        ), f"[{value}] price mismatch"
        assert row["value"] == value, f"[{value}] value mismatch"

    n_snapshot = len(snapshot_rows)
    n_total = len(rows_data)

    with postgres.publication(table_name) as publication_name:
        table = pw.io.postgres.read(
            postgres_settings=POSTGRES_SETTINGS,
            table_name=table_name,
            schema=InputSchema,
            mode="streaming",
            publication_name=publication_name,
            autocommit_duration_ms=10,
        )
        pw.io.jsonlines.write(table, output_path)

        (rid, birthday, mtime, mtimetz, ip, net, mac, oid, price, val) = (
            streaming_row_data
        )

        def stream_target():
            wait_result_with_checker(
                FileLinesNumberChecker(output_path, n_snapshot), 30, target=None
            )
            postgres.execute_sql(
                f"""
                INSERT INTO {table_name}
                (id, birthday, meeting_time, meeting_timetz, ip_addr, network, mac_addr, object_id, price, value)
                VALUES (
                    '{rid}', '{birthday}', '{mtime}', '{mtimetz}',
                    '{ip}', '{net}', '{mac}', {oid}, {price}, '{val}'
                );
                """
            )

        stream_thread = threading.Thread(target=stream_target, daemon=True)
        stream_thread.start()
        wait_result_with_checker(FileLinesNumberChecker(output_path, n_total), 30)

    rows_out = []
    with open(output_path) as f:
        for line in f:
            rows_out.append(json.loads(line))

    assert len(rows_out) == n_total

    id_to_row = {r["id"]: r for r in rows_out}

    # Verify all snapshot rows
    for row_data in snapshot_rows:
        rid, *_, val = row_data
        assert rid in id_to_row, f"Missing row {rid} ({val})"
        assert_row(id_to_row[rid], val)

    # Verify streaming row
    rid, *_, val = streaming_row_data
    assert rid in id_to_row, f"Missing streaming row {rid} ({val})"
    assert_row(id_to_row[rid], val)