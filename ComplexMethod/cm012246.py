def _parse_events(self, data: dict[str, Any]) -> None:
        events = data.get("traceEvents", [])
        # Reuse profile_analysis's External id -> CPU op mapping
        try:
            extern_mapping = _create_extern_mapping(data)
        except (ParseException, KeyError):
            # Malformed trace (e.g. duplicate External ids, missing traceEvents)
            extern_mapping = defaultdict(list)
            for ev in events:
                if (
                    isinstance(ev, dict)
                    and ev.get("cat") == "cpu_op"
                    and "args" in ev
                    and "External id" in ev["args"]
                ):
                    extern_mapping[ev["args"]["External id"]].append(ev)

        # Build External id -> total GPU kernel duration
        gpu_dur: dict[int, float] = defaultdict(float)
        for ev in events:
            if not isinstance(ev, dict) or ev.get("cat") != "kernel":
                continue
            args = ev.get("args", {})
            eid = args.get("External id")
            dur = ev.get("dur", 0.0)
            if eid is not None and dur > 0:
                gpu_dur[eid] += dur

        # Parse collectives from GPU kernel events directly
        # (NCCL kernels carry collective metadata in args)
        for ev in events:
            if not isinstance(ev, dict) or ev.get("cat") != "kernel":
                continue
            args = ev.get("args", {})
            coll_name = args.get("Collective name")
            if coll_name is None:
                continue
            pg_name = args.get("Process Group Name", "")
            pg_ranks_str = args.get("Process Group Ranks", "")
            group_size = args.get("Group size", 0)
            in_nelems = args.get("In msg nelems", 0)
            out_nelems = args.get("Out msg nelems", 0)
            dtype = args.get("dtype", "")
            dur = ev.get("dur", 0.0)
            if dur <= 0:
                continue

            pg_ranks = self._parse_ranks(pg_ranks_str, pg_name)

            self.collectives.append(
                CollectiveRecord(
                    collective_name=coll_name,
                    pg_ranks=pg_ranks,
                    group_size=group_size,
                    in_nelems=in_nelems,
                    out_nelems=out_nelems,
                    dtype=dtype,
                    duration_us=dur,
                )
            )

        # Parse all CPU ops that have associated GPU kernels
        for eid, cpu_evs in extern_mapping.items():
            if not cpu_evs:
                continue
            total_dur = gpu_dur.get(eid, 0.0)
            if total_dur <= 0:
                continue
            cpu_ev = cpu_evs[0]
            self._parse_op(cpu_ev.get("name", ""), cpu_ev.get("args", {}), total_dur)