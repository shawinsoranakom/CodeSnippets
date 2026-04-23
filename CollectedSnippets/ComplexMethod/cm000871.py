def test_transcript_builder_resume_after_compaction(self):
        """Simulates the full resume flow after a compacted transcript is
        uploaded and downloaded on the next turn."""
        # Turn N: compaction happened, upload compacted transcript
        compacted = _messages_to_transcript(
            [
                {"role": "user", "content": "[Summary of turns 1-10]"},
                {"role": "assistant", "content": "Summarized response"},
            ]
        )
        assert validate_transcript(compacted)

        # Turn N+1: download and load compacted transcript
        builder = TranscriptBuilder()
        builder.load_previous(compacted)
        assert builder.entry_count == 2

        # Append new turn
        builder.append_user("Turn N+1 question")
        builder.append_assistant(
            [{"type": "text", "text": "Turn N+1 answer"}], model="test"
        )
        assert builder.entry_count == 4

        # Verify output is valid
        output = builder.to_jsonl()
        assert validate_transcript(output)

        # Verify parent chain is correct
        entries = [json.loads(line) for line in output.strip().split("\n")]
        for i in range(1, len(entries)):
            assert entries[i]["parentUuid"] == entries[i - 1]["uuid"]