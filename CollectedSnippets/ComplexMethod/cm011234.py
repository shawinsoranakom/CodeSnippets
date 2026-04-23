def to_collective(
        self,
        id: int,
        errors: set[tuple[int, MatchInfo]] | None = None,
        idx_map: dict[int, int] | None = None,
        all_entries: dict[int, list[dict[str, Any]]] | None = None,
    ) -> Collective:
        if not errors:
            return Collective(
                id=id,
                group_id=self.pg_name,
                record_id=self.record_id,
                pg_desc=self.pg_desc,
                pass_check=True,
                collective_seq_id=self.collective_seq_id,
                p2p_seq_id=self.p2p_seq_id,
                collective_name=self.profiling_name,
                input_sizes=self.input_sizes,
                output_sizes=self.output_sizes,
                expected_ranks=self.expected_ranks,
                collective_state=self.collective_state,
                collective_frames=self.collective_frames,
                missing_ranks=getattr(self, "missing_ranks", None),
            )
        else:
            if idx_map is None:
                raise AssertionError("idx_map is None")
            if all_entries is None:
                raise AssertionError("all_entries is None")
            mismatch_collectives = {}
            for rank, error in errors:
                idx = idx_map[rank]
                entry = all_entries[rank][idx]
                desc = entry["process_group"][1]
                pg_name = entry["process_group"][0]
                mismatch_collectives[rank] = Collective(
                    id=id,
                    group_id=entry["process_group"][0],
                    record_id=entry["record_id"],
                    pg_desc=f"{pg_name}:{desc}" if desc != "undefined" else pg_name,
                    pass_check=False,
                    collective_seq_id=entry["collective_seq_id"],
                    p2p_seq_id=entry["p2p_seq_id"],
                    collective_name=entry["profiling_name"],
                    input_sizes=entry["input_sizes"],
                    output_sizes=entry["output_sizes"],
                    expected_ranks=self.expected_ranks,
                    collective_state=entry["state"],
                    collective_frames=entry.get("frames", []),
                    type_of_mismatch=error,
                )
            return Collective(
                id=id,
                group_id=self.pg_name,
                record_id=self.record_id,
                pg_desc=self.pg_desc,
                pass_check=False,
                collective_seq_id=self.collective_seq_id,
                p2p_seq_id=self.p2p_seq_id,
                collective_name=self.profiling_name,
                input_sizes=self.input_sizes,
                output_sizes=self.output_sizes,
                expected_ranks=self.expected_ranks,
                collective_state=self.collective_state,
                collective_frames=self.collective_frames,
                input_numel=self.input_numel if hasattr(self, "input_numel") else None,
                output_numel=self.output_numel
                if hasattr(self, "output_numel")
                else None,
                missing_ranks=self.missing_ranks
                if hasattr(self, "missing_ranks")
                else None,
                mismatch_collectives=mismatch_collectives,
            )