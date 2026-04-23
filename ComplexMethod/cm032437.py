def test_multiple_kb_ids_aggregated_separately(self, call_with_rows):
        rows = [
            {"kb_id": "kb-a", "run": TaskStatus.DONE.value, "cnt": 5},
            {"kb_id": "kb-a", "run": TaskStatus.FAIL.value, "cnt": 1},
            {"kb_id": "kb-b", "run": TaskStatus.UNSTART.value, "cnt": 7},
            {"kb_id": "kb-b", "run": TaskStatus.DONE.value, "cnt": 2},
        ]
        result = call_with_rows(rows=rows, kb_ids=["kb-a", "kb-b"])

        assert set(result.keys()) == {"kb-a", "kb-b"}

        assert result["kb-a"]["done_count"] == 5
        assert result["kb-a"]["fail_count"] == 1
        assert result["kb-a"]["unstart_count"] == 0
        assert result["kb-a"]["running_count"] == 0
        assert result["kb-a"]["cancel_count"] == 0

        assert result["kb-b"]["unstart_count"] == 7
        assert result["kb-b"]["done_count"] == 2
        assert result["kb-b"]["fail_count"] == 0