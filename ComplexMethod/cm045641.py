def test_persistence_modifications(tmp_path, scenario):
    inputs_path = tmp_path / "inputs"
    output_path = tmp_path / "output.txt"
    pstorage_path = tmp_path / "PStorage"
    os.mkdir(inputs_path)

    def pw_identity_program():
        G.clear()
        persistence_backend = pw.persistence.Backend.filesystem(pstorage_path)
        persistence_config = pw.persistence.Config(persistence_backend)
        table = pw.io.plaintext.read(inputs_path, mode="static")
        pw.io.jsonlines.write(table, output_path)
        pw.run(persistence_config=persistence_config)

    file_contents: dict[str, str] = {}
    next_file_contents = 0
    for sequence in scenario:
        expected_diffs = []
        for command in sequence:
            used_file_ids = set()
            if command.startswith("Upsert(") and command.endswith(")"):
                file_id = command[len("Upsert(") : -1]
                assert (
                    file_id not in used_file_ids
                ), "Incorrect scenario! File changed more than once in a single sequence"
                used_file_ids.add(file_id)

                # Record old state removal
                old_contents = file_contents.get(file_id)
                if old_contents is not None:
                    expected_diffs.append([old_contents, -1])

                # Handle new state change
                next_file_contents += 1
                new_contents = (
                    "a" * next_file_contents
                )  # This way, the metadata always changes: at least the file size
                file_contents[file_id] = new_contents
                expected_diffs.append([new_contents, 1])
                with open(inputs_path / file_id, "w") as f:
                    f.write(new_contents)
            elif command.startswith("Delete(") and command.endswith(")"):
                file_id = command[len("Delete(") : -1]
                assert (
                    file_id not in used_file_ids
                ), "Incorrect scenario! File changed more than once in a single sequence"
                used_file_ids.add(file_id)

                old_contents = file_contents.pop(file_id, None)
                assert (
                    old_contents is not None
                ), f"Incorrect scenario! Deletion of a nonexistent object {scenario}"
                expected_diffs.append([old_contents, -1])
                os.remove(inputs_path / file_id)
            else:
                raise ValueError(f"Unknown command: {command}")

        pw_identity_program()
        actual_diffs = []
        with open(output_path, "r") as f:
            for row in f:
                row_parsed = json.loads(row)
                actual_diffs.append([row_parsed["data"], row_parsed["diff"]])
        actual_diffs.sort()
        expected_diffs.sort()
        assert actual_diffs == expected_diffs