def compute_branch_diffs(
        self, from_branch: str, to_branch: str
    ) -> tuple[list[str], list[str]]:
        """
        Returns list of commits that are missing in each other branch since their merge base
        Might be slow if merge base is between two branches is pretty far off
        """
        from_ref = self.rev_parse(from_branch)
        to_ref = self.rev_parse(to_branch)
        merge_base = self.get_merge_base(from_ref, to_ref)
        from_commits = self.revlist(f"{merge_base}..{from_ref}")
        to_commits = self.revlist(f"{merge_base}..{to_ref}")
        from_ids = fuzzy_list_to_dict(self.patch_id(from_commits))
        to_ids = fuzzy_list_to_dict(self.patch_id(to_commits))
        for patch_id in set(from_ids).intersection(set(to_ids)):
            from_values = from_ids[patch_id]
            to_values = to_ids[patch_id]
            if len(from_values) != len(to_values):
                # Eliminate duplicate commits+reverts from the list
                while len(from_values) > 0 and len(to_values) > 0:
                    frc = self.get_commit(from_values.pop())
                    toc = self.get_commit(to_values.pop())
                    # FRC branch might have PR number added to the title
                    if frc.title != toc.title or frc.author_date != toc.author_date:
                        # HACK: Same commit were merged, reverted and landed again
                        # which creates a tracking problem
                        if (
                            "pytorch/pytorch" not in self.remote_url()
                            or frc.commit_hash
                            not in {
                                "0a6a1b27a464ba5be5f587cce2ee12ab8c504dbf",
                                "6d0f4a1d545a8f161df459e8d4ccafd4b9017dbe",
                                "edf909e58f06150f7be41da2f98a3b9de3167bca",
                                "a58c6aea5a0c9f8759a4154e46f544c8b03b8db1",
                                "7106d216c29ca16a3504aa2bedad948ebcf4abc2",
                            }
                        ):
                            raise RuntimeError(
                                f"Unexpected differences between {frc} and {toc}"
                            )
                    from_commits.remove(frc.commit_hash)
                    to_commits.remove(toc.commit_hash)
                continue
            for commit in from_values:
                from_commits.remove(commit)
            for commit in to_values:
                to_commits.remove(commit)
        # Another HACK: Patch-id is not stable for commits with binary files or for big changes across commits
        # I.e. cherry-picking those from one branch into another will change patchid
        if "pytorch/pytorch" in self.remote_url():
            for excluded_commit in {
                "8e09e20c1dafcdbdb45c2d1574da68a32e54a3a5",
                "5f37e5c2a39c3acb776756a17730b865f0953432",
                "b5222584e6d6990c6585981a936defd1af14c0ba",
                "84d9a2e42d5ed30ec3b8b4140c38dd83abbce88d",
                "f211ec90a6cdc8a2a5795478b5b5c8d7d7896f7e",
            }:
                if excluded_commit in from_commits:
                    from_commits.remove(excluded_commit)

        return (from_commits, to_commits)