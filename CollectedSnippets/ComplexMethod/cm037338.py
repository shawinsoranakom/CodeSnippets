def _create_sm_control_context(vllm_config: VllmConfig):
        comm_sms: int = envs.VLLM_DBO_COMM_SMS

        set_comm_sms = lambda sms: None
        if vllm_config.parallel_config.enable_expert_parallel:
            # Currently only DeepEP highthroughput supports SM control so this
            # only affects that case.
            ep_group = get_ep_group()
            device_communicator = ep_group.device_communicator
            all2all_manager = None
            if device_communicator is not None:
                all2all_manager = device_communicator.all2all_manager

            if all2all_manager is not None:
                max_sms_used = all2all_manager.max_sms_used()
                if max_sms_used is not None:
                    comm_sms = min(comm_sms, max_sms_used)

            if comm_sms > 0 and all2all_manager is not None:
                set_comm_sms = lambda sms: all2all_manager.set_num_sms(sms)

        # TODO(lucas): support other kernels besides DeepGEMM
        set_compute_sms = lambda sms: None
        if has_deep_gemm() and comm_sms > 0:
            set_compute_sms = lambda sms: deep_gemm_set_num_sms(sms)

        return SMControlContextManager(
            comm_sms=comm_sms,
            set_comm_sms=set_comm_sms,
            set_compute_sms=set_compute_sms,
        )