def test_pool_id_in_snapshot(self):
        try:
            torch.cuda.memory.empty_cache()
            torch.cuda.memory._record_memory_history("all")

            pool = torch.cuda.MemPool()
            with torch.cuda.use_mem_pool(pool):
                x = torch.rand(64, device="cuda")

            ss = torch.cuda.memory._snapshot()

            # segment_pool_id should match the MemPool id
            found_segment = False
            for seg in ss["segments"]:
                if seg["segment_pool_id"] == pool.id:
                    found_segment = True
                    break
            self.assertTrue(found_segment)

            # trace entries for this allocation should carry pool_id
            found_trace = False
            for trace in ss["device_traces"]:
                for te in trace:
                    if "pool_id" not in te:
                        continue
                    if te["pool_id"] == pool.id and te["action"] == "alloc":
                        found_trace = True
                        break
            self.assertTrue(found_trace)

            del x
        finally:
            torch.cuda.memory._record_memory_history(None)