def test_builder_load_then_replace_then_export_roundtrip(self):
        """Load a compacted transcript, replace with new compaction, export.
        Simulates two consecutive turns with compaction each time."""
        # Turn 1: load compacted transcript
        compact1 = {
            "type": "summary",
            "uuid": "cs1",
            "isCompactSummary": True,
            "message": {"role": "user", "content": "summary v1"},
        }
        asst1 = {
            "type": "assistant",
            "uuid": "a1",
            "parentUuid": "cs1",
            "message": {"role": "assistant", "content": "response 1"},
        }
        builder = TranscriptBuilder()
        builder.load_previous(_make_jsonl(compact1, asst1))
        assert builder.entry_count == 2

        # Turn 1: append new messages
        builder.append_user("question")
        builder.append_assistant([{"type": "text", "text": "answer"}])
        assert builder.entry_count == 4

        # Turn 1: compaction fires — replace with new compacted state
        compact2 = {
            "type": "summary",
            "uuid": "cs2",
            "isCompactSummary": True,
            "message": {"role": "user", "content": "summary v2"},
        }
        asst2 = {
            "type": "assistant",
            "uuid": "a2",
            "parentUuid": "cs2",
            "message": {"role": "assistant", "content": "continuing"},
        }
        builder.replace_entries([compact2, asst2])
        assert builder.entry_count == 2

        # Export (this goes to cloud storage for next turn's download)
        output = builder.to_jsonl()
        lines = [json.loads(line) for line in output.strip().split("\n")]
        assert lines[0]["uuid"] == "cs2"
        assert lines[0]["type"] == "summary"
        assert lines[1]["uuid"] == "a2"

        # Turn 2: fresh builder loads the exported transcript
        builder2 = TranscriptBuilder()
        builder2.load_previous(output)
        assert builder2.entry_count == 2
        builder2.append_user("turn 2 question")
        output2 = builder2.to_jsonl()
        lines2 = [json.loads(line) for line in output2.strip().split("\n")]
        assert lines2[-1]["parentUuid"] == "a2"