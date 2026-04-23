def warmup(fn, model, example_inputs, mode, niters=5):
            gc.collect()
            peak_mem = 0
            start_stats = get_dynamo_stats()
            try:
                if current_device == "cuda":
                    torch.cuda.reset_peak_memory_stats()
                    empty_gpu_cache(current_device)
                elif current_device == "hpu":
                    torch.hpu.reset_peak_memory_stats()
                t0 = time.perf_counter()
                for _ in range(niters):
                    fn(model, example_inputs)
                t1 = time.perf_counter()
                latency = t1 - t0
                if current_device == "cuda":
                    peak_mem = get_peak_memory()
                elif current_device == "hpu":
                    peak_mem = torch.hpu.max_memory_allocated() / 10**9
                elif current_device == "cpu":
                    total = psutil.virtual_memory().total
                    percentage = psutil.Process(os.getpid()).memory_percent()
                    peak_mem = percentage * total / 10**9
            except Exception:
                log.exception("Backend %s failed in warmup()", mode)
                write_csv_when_exception(
                    self.args, current_name, "warmup_failed", current_device
                )
                output_signpost({}, self.args, self.suite_name, error="warmup_failed")
                return sys.exit(-1)
            dynamo_stats = get_dynamo_stats()
            dynamo_stats.subtract(start_stats)
            return latency, peak_mem, dynamo_stats