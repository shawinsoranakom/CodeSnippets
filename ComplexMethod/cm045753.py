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