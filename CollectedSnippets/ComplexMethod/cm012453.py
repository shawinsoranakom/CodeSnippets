def parallel(self, threads):
        if self.in_parallel and threads != self.num_threads:
            # wrong number of threads
            self.close()
        if not self.in_parallel:
            self.num_threads = threads
            self.in_parallel = True
            # Decide whether to use dynamic threading
            use_dynamic = False
            if config.cpp.threads >= 1:
                # User explicitly set config.cpp.threads (hardcode it)
                use_dynamic = False
            elif threads == os.cpu_count():
                # Thread count matches system CPU count (most likely default, use dynamic)
                use_dynamic = True
            else:
                # Thread count differs from system (user probably set it so hardcode)
                use_dynamic = False

            if use_dynamic or config.cpp.dynamic_threads:
                self.code.writeline("#pragma omp parallel")
            else:
                self.code.writeline(f"#pragma omp parallel num_threads({threads})")
            self.stack.enter_context(self.code.indent())
            self.code.writeline(
                "int tid = omp_get_thread_num();",
            )