def __init__(
        self, event: dict[Any, Any], memberships: dict[str, set[Any]], pg_name: str
    ):
        self.profiling_name = event["profiling_name"]
        comm_lib_backend, name = self.profiling_name.split(":")
        if comm_lib_backend not in ["nccl", "ncclx", "gloo", "xccl"]:
            raise AssertionError(
                f"name formatting error? {comm_lib_backend} not in supported backends"
            )
        parts = name.split(" ")
        type = parts[0]
        meta = parts[1] if len(parts) == 2 else None
        self.state = event["state"]
        # Store the hashed pg_name for accessing memberships, and original pg info for display
        self.pg_name = pg_name  # This is the hashed version used for memberships lookup
        self.original_pg_name, self.pg_desc = event["process_group"]
        if type not in COLLECTIVES | P2P | {"coalesced"}:
            raise AssertionError(f"{type} is not a supported operation")
        self.type = type
        if type == "send":
            if not isinstance(meta, str):
                raise AssertionError
            s, d = meta.split("->")
            self._src, self._dst = int(s), int(d)
        elif type == "recv":
            if not isinstance(meta, str):
                raise AssertionError
            d, s = meta.split("<-")
            self._dst, self._src = int(d), int(s)
        else:
            self._src, self._dst = -1, -1
        self._init_global_src_dst(memberships[pg_name])
        self.pg_size = len(memberships[pg_name])
        if type in P2P | COLLECTIVES:
            self.input_sizes = event["input_sizes"]
            self.output_sizes = event["output_sizes"]
        else:
            self.input_sizes, self.output_sizes = None, None
        self.collective_seq_id = event["collective_seq_id"]
        self.stack_id = event.get("stack_id", -1)
        self.p2p_seq_id = event["p2p_seq_id"]
        self.input_dtypes = event["input_dtypes"]
        self.output_dtypes = event["output_dtypes"]
        self.time_created_ns = event["time_created_ns"]
        self.collective_frames = event.get("frames", [])
        self.is_verbose = os.getenv("FR_TRACE_VERBOSE_OUTPUT", "0") == "1"