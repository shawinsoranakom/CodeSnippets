def match(self, other: "Op") -> MatchInfo:
        # TODO: I think this can validly not match,
        # e.g. if one PG was used for p2p ops between only some of the peers?
        # if self.seq_id != other.seq_id:
        # return False

        if self.type == "send":
            # TODO: We need more states for p2p ops.
            return (
                MatchInfo(MatchState.FULLY_MATCHED)
                if (
                    other.type == "recv"
                    and self.src == other.src
                    and self.dst == other.dst
                    and self.input_sizes == other.output_sizes
                )
                else MatchInfo(MatchState.SIZE_OR_SYNTAX_MISMATCH)
            )
        elif self.type == "recv":
            return (
                MatchInfo(MatchState.FULLY_MATCHED)
                if (
                    other.type == "send"
                    and self.src == other.src
                    and self.dst == other.dst
                    and self.output_sizes == other.input_sizes
                )
                else MatchInfo(MatchState.SIZE_OR_SYNTAX_MISMATCH)
            )
        elif self.type in COLLECTIVES:
            if self.type != other.type:
                return MatchInfo(
                    MatchState.COLLECTIVE_TYPE_MISMATCH,
                    f"Expected collective type: '{self.type}' does not match found collective type: '{other.type}'",
                )
            if (
                self.type not in ["all_to_all", "scatter"]
                and self.input_sizes != other.input_sizes
            ):
                return MatchInfo(
                    MatchState.SIZE_OR_SYNTAX_MISMATCH,
                    f"Expected input sizes: '{self.input_sizes}' does not match found input sizes: "
                    f"'{other.input_sizes}'",
                )
            if (
                self.type not in ["all_to_all", "gather"]
                and self.output_sizes != other.output_sizes
            ):
                return MatchInfo(
                    MatchState.SIZE_OR_SYNTAX_MISMATCH,
                    f"Expected output sizes: '{self.output_sizes}' does not match found output sizes: "
                    f"'{other.output_sizes}'",
                )
            if (
                self.type in ["all_reduce", "allreduce_coalesced"]
                and self.input_sizes != other.output_sizes
            ):
                return MatchInfo(
                    MatchState.SIZE_OR_SYNTAX_MISMATCH,
                    f"Expected input sizes: '{self.input_sizes}' does not match found output sizes: '{other.output_sizes}'",
                )
            if (
                self.type
                in [
                    "all_gather",
                    "all_gather_base",
                    "all_gather_into_tensor_coalesced",
                ]
                and math.prod(other.output_sizes[0])
                != math.prod(self.input_sizes[0]) * self.pg_size
            ):
                return MatchInfo(
                    MatchState.SIZE_OR_SYNTAX_MISMATCH,
                    f"Found input numel '{math.prod(other.input_sizes[0])} * pg size {self.pg_size}' "
                    f"does not match output numel '{math.prod(other.output_sizes[0])}'",
                )
            if (
                self.type
                in [
                    "reduce_scatter",
                    "_reduce_scatter_base",
                    "reduce_scatter_tensor_coalesced",
                ]
                and math.prod(other.input_sizes[0])
                != math.prod(self.output_sizes[0]) * self.pg_size
            ):
                return MatchInfo(
                    MatchState.SIZE_OR_SYNTAX_MISMATCH,
                    f"Found input numel '{math.prod(other.input_sizes[0])}' does not match output numel "
                    f"'{math.prod(other.output_sizes[0])} * pg size {self.pg_size}'",
                )
            if self.dtype_mismatch(other):
                return MatchInfo(
                    MatchState.COLLECTIVE_DTYPE_MISMATCH,
                    f"Expected dtypes: '{set(self.input_dtypes)}' does not "
                    f"match found dtype: '{set(self.output_dtypes)}/"
                    f"{set(other.input_dtypes)}/{set(other.output_dtypes)}'",
                )
            if self.state != other.state:
                # MatchState()
                return MatchInfo(
                    MatchState.COLLECTIVE_STATE_MISMATCH,
                    f"Expected state: '{self.state}' does not match found state: '{other.state}'",
                )
            if self.type == "all_to_all":
                return MatchInfo(MatchState.UNDECIDED)
        elif self.type in [
            "coalesced",
            "ALLGATHER_coalesced",
            "REDUCE_SCATTER_coalesced",
        ]:
            return (
                MatchInfo(MatchState.FULLY_MATCHED)
                if (other.type == self.type)
                else MatchInfo(MatchState.SIZE_OR_SYNTAX_MISMATCH)
            )
        return MatchInfo(MatchState.FULLY_MATCHED)