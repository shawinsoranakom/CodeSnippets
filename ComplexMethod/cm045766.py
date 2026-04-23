def test_persistent_runs(tmp_path, scenario):
    inputs_path = tmp_path / "inputs"
    output_path = tmp_path / "output.jsonl"
    pstorage_path = tmp_path / "pstorage"
    persistence_config = pw.persistence.Config(
        backend=pw.persistence.Backend.filesystem(pstorage_path)
    )
    os.mkdir(inputs_path)
    n_total_upserts = 0
    current_objects_snapshot: dict[str, str] = {}
    expected_additions: list[list[str]] = []
    expected_deletions: list[list[str]] = []

    def run_pathway_program():
        G.clear()
        table = pw.io.plaintext.read(inputs_path, mode="static", with_metadata=True)
        pw.io.jsonlines.write(table, output_path)
        pw.run(persistence_config=persistence_config)
        factual_additions = []
        factual_deletions = []
        addition_bad_idx = []
        deletion_bad_idx = []
        with open(output_path, "r") as f:
            for row in f:
                parsed = json.loads(row)
                file_name = os.path.basename(parsed["_metadata"]["path"])
                contents = parsed["data"]
                if parsed["diff"] == 1:
                    factual_additions.append([file_name, contents])
                elif parsed["diff"] == -1:
                    factual_deletions.append([file_name, contents])
                else:
                    assert False, "incorrect diff: {}".format(parsed["diff"])

        for addition_idx, addition in enumerate(factual_additions):
            for deletion_idx, deletion in enumerate(factual_deletions):
                if addition == deletion:
                    # Owner changed from user to null or vice-versa, ignore such changes
                    addition_bad_idx.append(addition_idx)
                    deletion_bad_idx.append(deletion_idx)
        factual_additions = [
            item
            for i, item in enumerate(factual_additions)
            if i not in addition_bad_idx
        ]
        factual_deletions = [
            item
            for i, item in enumerate(factual_deletions)
            if i not in deletion_bad_idx
        ]

        factual_deletions.sort()
        factual_additions.sort()
        expected_additions.sort()
        expected_deletions.sort()
        assert factual_additions == expected_additions
        assert factual_deletions == expected_deletions

    # Check the states of all objects at the end, after the possible compression round
    all_object_ids = []
    for token in scenario:
        if token > 0 and token not in all_object_ids:
            all_object_ids.append(token)
    full_scenario = scenario + [0] + all_object_ids + [0]

    for token in full_scenario:
        file_name = str(abs(token))
        file_path = inputs_path / file_name
        if token > 0:
            n_total_upserts += 1
            file_contents = "a" * n_total_upserts

            old_contents = current_objects_snapshot.pop(file_name, None)
            if old_contents is not None:
                expected_deletions.append([file_name, old_contents])
            current_objects_snapshot[file_name] = file_contents
            expected_additions.append([file_name, file_contents])

            file_path.write_text(file_contents)
        elif token < 0:
            os.remove(file_path)
            old_contents = current_objects_snapshot.pop(file_name)
            expected_deletions.append([file_name, old_contents])
        else:
            run_pathway_program()
            expected_additions.clear()
            expected_deletions.clear()