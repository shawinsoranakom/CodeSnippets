def test_csv(self, csv_name):
        def _dump_csv(pipeline_order_with_comms, filename: str):
            """Dump a CSV representation of the compute + comms schedule into a file with the provided filename."""
            with open(filename, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                for rank in pipeline_order_with_comms:
                    writer.writerow(pipeline_order_with_comms[rank])

        compute_sch = {}
        with open(
            os.path.join(ARTIFACTS_DIR, f"{csv_name}_compute.csv"), newline=""
        ) as csvfile:
            for rank, row in enumerate(csv.reader(csvfile)):
                compute_sch[rank] = [_Action.from_str(s) for s in row]
        # print(_format_pipeline_order(compute_sch))
        num_model_chunks = 2
        pipeline_parallel_size = 2
        num_stages = num_model_chunks * pipeline_parallel_size

        for rank in compute_sch:
            compute_sch[rank] = _merge_bw(compute_sch[rank])

        comms_sch = _add_send_recv(
            compute_sch,
            stage_to_rank=lambda chunk_index: chunk_index % pipeline_parallel_size,
            num_stages=num_stages,
        )

        comms_csv = os.path.join(ARTIFACTS_DIR, f"{csv_name}_comms.csv")

        # Uncomment to regenerate reference output
        # _dump_csv(comms_sch, comms_csv)

        sch_ref = {}
        with open(comms_csv, newline="") as ref:
            for rank, row in enumerate(csv.reader(ref)):
                sch_ref[rank] = [_Action.from_str(s) for s in row]

        for rank in sch_ref:
            for timestep, (a, b) in enumerate(zip(comms_sch[rank], sch_ref[rank])):
                self.assertEqual(a, b, f"Mismatch at {timestep=}, {a=}, expected {b}")

        simulated_schedule = _simulate_comms_compute(
            comms_sch,
            stage_to_rank=lambda s: s % pipeline_parallel_size,
            num_stages=num_stages,
        )

        num_steps = max([len(simulated_schedule[rank]) for rank in simulated_schedule])
        # print(_format_pipeline_order(simulated_schedule))
        self.assertEqual(num_steps, 113)