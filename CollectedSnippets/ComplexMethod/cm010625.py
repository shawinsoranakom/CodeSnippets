def format(entries):
        segment_intervals: list = []
        segment_addr_to_name = {}
        allocation_addr_to_name = {}

        free_names: list = []
        next_name = 0

        def _name():
            nonlocal next_name
            if free_names:
                return free_names.pop()
            r, m = next_name // 26, next_name % 26
            next_name += 1
            return f"{chr(ord('a') + m)}{'' if r == 0 else r}"

        def find_segment(addr):
            for name, saddr, size in segment_intervals:
                if addr >= saddr and addr < saddr + size:
                    return name, saddr
            for i, seg in enumerate(data["segments"]):
                saddr = seg["address"]
                size = seg["allocated_size"]
                if addr >= saddr and addr < saddr + size:
                    return f"seg_{i}", saddr
            return None, None

        count = 0
        out.write(f"{len(entries)} entries\n")

        total_reserved = 0
        for seg in data["segments"]:
            total_reserved += seg["total_size"]

        for count, e in enumerate(entries):
            if e["action"] == "alloc":
                addr, size = e["addr"], e["size"]
                n = _name()
                seg_name, seg_addr = find_segment(addr)
                if seg_name is None:
                    seg_name = "MEM"
                    offset = addr
                else:
                    offset = addr - seg_addr
                out.write(f"{n} = {seg_name}[{offset}:{Bytes(size)}]\n")
                allocation_addr_to_name[addr] = (n, size, count)
                count += size
            elif e["action"] == "free_requested":
                addr, size = e["addr"], e["size"]
                name, _, _ = allocation_addr_to_name.get(addr, (addr, None, None))
                out.write(f"del {name} # {Bytes(size)}\n")
            elif e["action"] == "free_completed":
                addr, size = e["addr"], e["size"]
                count -= size
                name, _, _ = allocation_addr_to_name.get(addr, (addr, None, None))
                out.write(f"# free completed for {name} {Bytes(size)}\n")
                if name in allocation_addr_to_name:
                    free_names.append(name)
                    del allocation_addr_to_name[name]
            elif e["action"] == "segment_alloc":
                addr, size = e["addr"], e["size"]
                name = _name()
                out.write(f"{name} = cudaMalloc({addr}, {Bytes(size)})\n")
                segment_intervals.append((name, addr, size))
                segment_addr_to_name[addr] = name
            elif e["action"] == "segment_free":
                addr, size = e["addr"], e["size"]
                name = segment_addr_to_name.get(addr, addr)
                out.write(f"cudaFree({name}) # {Bytes(size)}\n")
                if name in segment_addr_to_name:
                    free_names.append(name)
                    del segment_addr_to_name[name]
            elif e["action"] == "oom":
                size = e["size"]
                free = e["device_free"]
                out.write(
                    f"raise OutOfMemoryError # {Bytes(size)} requested, {Bytes(free)} free in CUDA\n"
                )
            else:
                out.write(f"{e}\n")
        out.write(f"TOTAL MEM: {Bytes(count)}")