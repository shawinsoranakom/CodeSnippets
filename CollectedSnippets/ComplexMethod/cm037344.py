def init_worker(self, all_kwargs: list[dict[str, Any]]) -> None:
        """
        Here we inject some common logic before initializing the worker.
        Arguments are passed to the worker class constructor.
        """
        kwargs = all_kwargs[self.rpc_rank]

        vllm_config: VllmConfig | None = kwargs.get("vllm_config")
        assert vllm_config is not None, (
            "vllm_config is required to initialize the worker"
        )
        self.vllm_config = vllm_config

        vllm_config.enable_trace_function_call_for_thread()

        from vllm.plugins import load_general_plugins

        load_general_plugins()

        parallel_config = vllm_config.parallel_config
        if isinstance(parallel_config.worker_cls, str):
            worker_class: type[WorkerBase] = resolve_obj_by_qualname(
                parallel_config.worker_cls
            )
        else:
            raise ValueError(
                "passing worker_cls is no longer supported. "
                "Please pass keep the class in a separate module "
                "and pass the qualified name of the class as a string."
            )

        if parallel_config.worker_extension_cls:
            worker_extension_cls = resolve_obj_by_qualname(
                parallel_config.worker_extension_cls
            )
            extended_calls = []
            if worker_extension_cls not in worker_class.__bases__:
                # check any conflicts between worker and worker_extension_cls
                for attr in dir(worker_extension_cls):
                    if attr.startswith("__"):
                        continue
                    assert not hasattr(worker_class, attr), (
                        f"Worker class {worker_class} already has an attribute"
                        f" {attr}, which conflicts with the worker"
                        f" extension class {worker_extension_cls}."
                    )
                    if callable(getattr(worker_extension_cls, attr)):
                        extended_calls.append(attr)
                # dynamically inherit the worker extension class
                worker_class.__bases__ = worker_class.__bases__ + (
                    worker_extension_cls,
                )
                logger.info(
                    "Injected %s into %s for extended collective_rpc calls %s",
                    worker_extension_cls,
                    worker_class,
                    extended_calls,
                )

        shared_worker_lock = kwargs.pop("shared_worker_lock", None)
        if shared_worker_lock is None:
            msg = (
                "Missing `shared_worker_lock` argument from executor. "
                "This argument is needed for mm_processor_cache_type='shm'."
            )

            mm_config = vllm_config.model_config.multimodal_config
            if mm_config and mm_config.mm_processor_cache_type == "shm":
                raise ValueError(msg)
            else:
                logger.warning_once(msg)

            self.mm_receiver_cache = None
        else:
            self.mm_receiver_cache = (
                MULTIMODAL_REGISTRY.worker_receiver_cache_from_config(
                    vllm_config,
                    shared_worker_lock,
                )
            )

        with set_current_vllm_config(self.vllm_config):
            # To make vLLM config available during worker initialization
            self.worker = worker_class(**kwargs)