def _save_rng_state(self, output_dir: str) -> None:
        """Save random number generator states for reproducible resumption."""
        # Save RNG state in non-distributed training
        rng_states = {
            "python": random.getstate(),
            "numpy": np.random.get_state(),
            "cpu": torch.random.get_rng_state(),
        }
        if torch.cuda.is_available():
            if self.args.parallel_mode == ParallelMode.DISTRIBUTED:
                # In non distributed, we save the global CUDA RNG state (will take care of DataParallel)
                rng_states["cuda"] = torch.cuda.random.get_rng_state_all()
            else:
                rng_states["cuda"] = torch.cuda.random.get_rng_state()

        if is_torch_xla_available():
            rng_states["xla"] = xm.get_rng_state()

        if is_torch_npu_available():
            if self.args.parallel_mode == ParallelMode.DISTRIBUTED:
                rng_states["npu"] = torch.npu.random.get_rng_state_all()
            else:
                rng_states["npu"] = torch.npu.random.get_rng_state()

        if is_torch_hpu_available():
            if self.args.parallel_mode == ParallelMode.DISTRIBUTED:
                rng_states["hpu"] = torch.hpu.random.get_rng_state_all()
            else:
                rng_states["hpu"] = torch.hpu.random.get_rng_state()

        if is_torch_mlu_available():
            if self.args.parallel_mode == ParallelMode.DISTRIBUTED:
                rng_states["mlu"] = torch.mlu.random.get_rng_state_all()
            else:
                rng_states["mlu"] = torch.mlu.random.get_rng_state()

        if is_torch_musa_available():
            if self.args.parallel_mode == ParallelMode.DISTRIBUTED:
                rng_states["musa"] = torch.musa.get_rng_state_all()
            else:
                rng_states["musa"] = torch.musa.get_rng_state()

        # A process can arrive here before the process 0 has a chance to save the model, in which case output_dir may
        # not yet exist.
        os.makedirs(output_dir, exist_ok=True)

        if self.args.world_size <= 1:
            torch.save(rng_states, os.path.join(output_dir, "rng_state.pth"))
        else:
            torch.save(rng_states, os.path.join(output_dir, f"rng_state_{self.args.process_index}.pth"))