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