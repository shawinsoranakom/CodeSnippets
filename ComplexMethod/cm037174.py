def _compiled_ray_dag(self, enable_asyncio: bool):
        assert self.parallel_config.use_ray
        self._check_ray_cgraph_installation()
        # Enlarge the default value of "RAY_CGRAPH_get_timeout" to 300 seconds
        # (it is 10 seconds by default). This is a Ray environment variable to
        # control the timeout of getting result from a compiled graph execution,
        # i.e., the distributed execution that includes model forward runs and
        # intermediate tensor communications, in the case of vllm.
        # Note: we should set this env var before importing
        # ray.dag, otherwise it will not take effect.
        os.environ.setdefault("RAY_CGRAPH_get_timeout", "300")  # noqa: SIM112
        from ray.dag import InputNode, MultiOutputNode

        logger.info(
            "RAY_CGRAPH_get_timeout is set to %s",
            os.environ["RAY_CGRAPH_get_timeout"],  # noqa: SIM112
        )
        logger.info(
            "VLLM_USE_RAY_COMPILED_DAG_CHANNEL_TYPE = %s",
            envs.VLLM_USE_RAY_COMPILED_DAG_CHANNEL_TYPE,
        )
        logger.info(
            "VLLM_USE_RAY_COMPILED_DAG_OVERLAP_COMM = %s",
            envs.VLLM_USE_RAY_COMPILED_DAG_OVERLAP_COMM,
        )

        channel_type = envs.VLLM_USE_RAY_COMPILED_DAG_CHANNEL_TYPE
        if channel_type not in ("auto", "nccl", "shm"):
            raise ValueError(
                "Invalid value for VLLM_USE_RAY_COMPILED_DAG_CHANNEL_TYPE: "
                f"{channel_type}. Valid values are: 'auto', 'nccl', or 'shm'."
            )

        with InputNode() as input_data:
            # Example DAG: PP=2, TP=4
            #
            # SchedulerOutput -> 0 -> (SchedulerOutput, IntermediateTensors) -> 4 -> ModelRunnerOutput   # noqa: E501
            # SchedulerOutput -> 1 -> (SchedulerOutput, IntermediateTensors) -> 5 -> ModelRunnerOutput   # noqa: E501
            # SchedulerOutput -> 2 -> (SchedulerOutput, IntermediateTensors) -> 6 -> ModelRunnerOutput   # noqa: E501
            # SchedulerOutput -> 3 -> (SchedulerOutput, IntermediateTensors) -> 7 -> ModelRunnerOutput   # noqa: E501

            # All workers in the first TP group will take in the
            # ExecuteModelRequest as input.
            outputs = [input_data for _ in self.pp_tp_workers[0]]
            for pp_rank, tp_group in enumerate(self.pp_tp_workers):
                # Each PP worker takes in the output of the previous PP worker,
                # and the TP group executes in SPMD fashion.
                outputs = [
                    worker.execute_model_ray.bind(outputs[i])  # type: ignore[attr-defined]
                    for i, worker in enumerate(tp_group)
                ]

                last_pp_rank = len(self.pp_tp_workers) - 1
                if (
                    pp_rank < last_pp_rank
                    and envs.VLLM_USE_RAY_COMPILED_DAG_CHANNEL_TYPE != "shm"
                ):
                    # Specify how intermediate tensors should be passed
                    # between pp stages, no need to specify for the last
                    # pp stage or when using shared memory (the default).
                    transport = envs.VLLM_USE_RAY_COMPILED_DAG_CHANNEL_TYPE
                    outputs = [
                        output.with_tensor_transport(transport=transport)
                        for output in outputs
                    ]

            forward_dag = MultiOutputNode(outputs)

        if envs.VLLM_USE_RAY_WRAPPED_PP_COMM:
            from ray.experimental.channel.accelerator_context import (
                register_accelerator_context,
            )

            from vllm.distributed.device_communicators.ray_communicator import (
                RayPPCommunicator,
            )

            register_accelerator_context(
                torch_module_name="cuda", communicator_cls=RayPPCommunicator
            )
            logger.info(
                "Using RayPPCommunicator "
                "(which wraps vLLM _PP GroupCoordinator) "
                "for Ray Compiled Graph communication."
            )
        else:
            logger.info(
                "Using Ray's NCCL communicator for Ray Compiled Graph communication."
            )

        return forward_dag.experimental_compile(
            enable_asyncio=enable_asyncio,
            _overlap_gpu_communication=envs.VLLM_USE_RAY_COMPILED_DAG_OVERLAP_COMM,
        )