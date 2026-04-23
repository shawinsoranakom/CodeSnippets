def shard_model(self, model: HFModel) -> HFModel:
        init_mode = getattr(model, "_init_mode", "init_on_default")

        if init_mode == "init_on_rank0":
            if getattr(model.config, "tie_word_embeddings", False):
                model.tie_weights()

            if self.rank == 0:
                logger.info("init_on_rank0 detected: sharding then scattering Rank 0 CPU weights.")
                full_sd = {k: v.clone() for k, v in model.state_dict().items()}
            else:
                full_sd = {}

            # Reuse existing helper to save persistent=False buffers (e.g. inv_freq) before shard
            saved_buffers = self._save_non_persistent_buffers(model) if self.rank == 0 else {}

            model = self.prepare_model(model)

            device = get_current_accelerator()
            model.to_empty(device=device)

            # Scatter params from Rank 0 into all DTensor shards
            # Broadcast the full state dict from the global rank-0 process to all ranks in this group.
            options = StateDictOptions(full_state_dict=True, cpu_offload=True, broadcast_from_rank0=True)
            set_model_state_dict(model, full_sd, options=options)

            # Broadcast and restore non-persistent buffers
            buffers_to_sync = [saved_buffers]
            dist.broadcast_object_list(buffers_to_sync, src=0, group=self.fsdp_mesh.get_group())
            self._restore_non_persistent_buffers(model, buffers_to_sync[0])

            if self.rank == 0:
                logger.info("init_on_rank0 sync complete.")

        elif init_mode == "init_on_meta":
            non_persistent_buffers = self._save_non_persistent_buffers(model)

            if getattr(model.config, "tie_word_embeddings", False):
                model.tie_weights()

            model = self.prepare_model(model)
            model = self.materialize_and_load(model, hf_model_path=model.config.name_or_path, dcp_path=self.dcp_path)

            # fix tied broken for no-fsdp-wrap case
            if getattr(model.config, "tie_word_embeddings", False):
                model.tie_weights()

            self._restore_non_persistent_buffers(model, non_persistent_buffers)

        else:
            model = self.prepare_model(model)

        self._warmup_grad_norm(model)

        return model