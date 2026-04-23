def __init__(
        self, vllm_config: VllmConfig, engine_indexes: list[int] | None = None
    ):
        if engine_indexes is None:
            engine_indexes = [0]

        self.engine_indexes = engine_indexes

        unregister_vllm_metrics()
        self.vllm_config = vllm_config
        # Use this flag to hide metrics that were deprecated in
        # a previous release and which will be removed future
        self.show_hidden_metrics = vllm_config.observability_config.show_hidden_metrics
        self.kv_cache_metrics_enabled = (
            vllm_config.observability_config.kv_cache_metrics
        )

        labelnames = ["model_name", "engine"]
        model_name = vllm_config.model_config.served_model_name
        max_model_len = vllm_config.model_config.max_model_len

        self.per_engine_labelvalues: dict[int, list[object]] = {
            idx: [model_name, str(idx)] for idx in engine_indexes
        }
        per_engine_labelvalues = self.per_engine_labelvalues

        self.spec_decoding_prom = self._spec_decoding_cls(
            vllm_config.speculative_config, labelnames, per_engine_labelvalues
        )
        self.kv_connector_prom = self._kv_connector_cls(
            vllm_config, labelnames, per_engine_labelvalues
        )
        self.perf_metrics_prom = self._perf_metrics_cls(
            vllm_config, labelnames, per_engine_labelvalues
        )

        #
        # Scheduler state
        #
        gauge_scheduler_running = self._gauge_cls(
            name="vllm:num_requests_running",
            documentation="Number of requests in model execution batches.",
            multiprocess_mode="mostrecent",
            labelnames=labelnames,
        )
        self.gauge_scheduler_running = create_metric_per_engine(
            gauge_scheduler_running, per_engine_labelvalues
        )

        gauge_scheduler_waiting = self._gauge_cls(
            name="vllm:num_requests_waiting",
            documentation="Number of requests waiting to be processed.",
            multiprocess_mode="mostrecent",
            labelnames=labelnames,
        )
        self.gauge_scheduler_waiting = create_metric_per_engine(
            gauge_scheduler_waiting, per_engine_labelvalues
        )

        gauge_waiting_by_reason = self._gauge_cls(
            name="vllm:num_requests_waiting_by_reason",
            documentation=(
                "Number of waiting requests by reason. "
                "Reason labels: 'capacity' = waiting for scheduling capacity; "
                "'deferred' = deferred by transient constraints "
                "(LoRA budget, KV transfer, blocked status). "
                "Sum of all reasons equals vllm:num_requests_waiting."
            ),
            multiprocess_mode="mostrecent",
            labelnames=labelnames + ["reason"],
        )
        self.gauge_waiting_by_reason: dict[str, dict[int, Gauge]] = {}
        for waiting_reason in [WAITING_REASON_CAPACITY, WAITING_REASON_DEFERRED]:
            per_engine_labelvalues_with_reason = {
                idx: labelvalues + [waiting_reason]
                for idx, labelvalues in per_engine_labelvalues.items()
            }
            self.gauge_waiting_by_reason[waiting_reason] = create_metric_per_engine(
                gauge_waiting_by_reason, per_engine_labelvalues_with_reason
            )

        gauge_engine_sleep_state = self._gauge_cls(
            name="vllm:engine_sleep_state",
            documentation=(
                "Engine sleep state; awake = 0 means engine is sleeping; "
                "awake = 1 means engine is awake; "
                "weights_offloaded = 1 means sleep level 1; "
                "discard_all = 1 means sleep level 2."
            ),
            labelnames=labelnames + ["sleep_state"],
            multiprocess_mode="mostrecent",
        )

        self.gauge_engine_sleep_state = {}
        sleep_state = ["awake", "weights_offloaded", "discard_all"]

        for s in sleep_state:
            self.gauge_engine_sleep_state[s] = {
                idx: gauge_engine_sleep_state.labels(
                    engine=idx, model_name=model_name, sleep_state=s
                )
                for idx in engine_indexes
            }

        # Setting default values
        self.record_sleep_state()

        gauge_kv_cache_usage = self._gauge_cls(
            name="vllm:kv_cache_usage_perc",
            documentation="KV-cache usage. 1 means 100 percent usage.",
            multiprocess_mode="mostrecent",
            labelnames=labelnames,
        )
        self.gauge_kv_cache_usage = create_metric_per_engine(
            gauge_kv_cache_usage, per_engine_labelvalues
        )

        if envs.VLLM_COMPUTE_NANS_IN_LOGITS:
            counter_corrupted_requests = self._counter_cls(
                name="vllm:corrupted_requests",
                documentation=(
                    "Corrupted requests, in terms of total number of requests "
                    "with NaNs in logits."
                ),
                labelnames=labelnames,
            )
            self.counter_corrupted_requests = create_metric_per_engine(
                counter_corrupted_requests, per_engine_labelvalues
            )

        counter_prefix_cache_queries = self._counter_cls(
            name="vllm:prefix_cache_queries",
            documentation=(
                "Prefix cache queries, in terms of number of queried tokens."
            ),
            labelnames=labelnames,
        )
        self.counter_prefix_cache_queries = create_metric_per_engine(
            counter_prefix_cache_queries, per_engine_labelvalues
        )

        counter_prefix_cache_hits = self._counter_cls(
            name="vllm:prefix_cache_hits",
            documentation=("Prefix cache hits, in terms of number of cached tokens."),
            labelnames=labelnames,
        )
        self.counter_prefix_cache_hits = create_metric_per_engine(
            counter_prefix_cache_hits, per_engine_labelvalues
        )

        #
        # External - KV connector prefix cache
        #

        counter_connector_prefix_cache_queries = self._counter_cls(
            name="vllm:external_prefix_cache_queries",
            documentation=(
                "External prefix cache queries from KV connector "
                "cross-instance cache sharing, in terms of number of queried tokens."
            ),
            labelnames=labelnames,
        )
        self.counter_connector_prefix_cache_queries = create_metric_per_engine(
            counter_connector_prefix_cache_queries, per_engine_labelvalues
        )

        counter_connector_prefix_cache_hits = self._counter_cls(
            name="vllm:external_prefix_cache_hits",
            documentation=(
                "External prefix cache hits from KV connector "
                "cross-instance cache sharing, in terms of number of cached tokens."
            ),
            labelnames=labelnames,
        )
        self.counter_connector_prefix_cache_hits = create_metric_per_engine(
            counter_connector_prefix_cache_hits, per_engine_labelvalues
        )

        #
        # Multi-modal cache
        #

        counter_mm_cache_queries = self._counter_cls(
            name="vllm:mm_cache_queries",
            documentation=(
                "Multi-modal cache queries, in terms of number of queried items."
            ),
            labelnames=labelnames,
        )
        self.counter_mm_cache_queries = create_metric_per_engine(
            counter_mm_cache_queries, per_engine_labelvalues
        )

        counter_mm_cache_hits = self._counter_cls(
            name="vllm:mm_cache_hits",
            documentation=(
                "Multi-modal cache hits, in terms of number of cached items."
            ),
            labelnames=labelnames,
        )
        self.counter_mm_cache_hits = create_metric_per_engine(
            counter_mm_cache_hits, per_engine_labelvalues
        )

        #
        # Counters
        #
        counter_num_preempted_reqs = self._counter_cls(
            name="vllm:num_preemptions",
            documentation="Cumulative number of preemption from the engine.",
            labelnames=labelnames,
        )
        self.counter_num_preempted_reqs = create_metric_per_engine(
            counter_num_preempted_reqs, per_engine_labelvalues
        )

        counter_prompt_tokens = self._counter_cls(
            name="vllm:prompt_tokens",
            documentation="Number of prefill tokens processed.",
            labelnames=labelnames,
        )
        self.counter_prompt_tokens = create_metric_per_engine(
            counter_prompt_tokens, per_engine_labelvalues
        )

        # Labeled prompt token counters by source
        counter_prompt_tokens_by_source = self._counter_cls(
            name="vllm:prompt_tokens_by_source",
            documentation="Number of prompt tokens by source.",
            labelnames=labelnames + ["source"],
        )
        self.counter_prompt_tokens_by_source: dict[str, dict[int, Counter]] = {}
        for source in PromptTokenStats.ALL_SOURCES:
            self.counter_prompt_tokens_by_source[source] = {
                idx: counter_prompt_tokens_by_source.labels(
                    model_name, str(idx), source
                )
                for idx in engine_indexes
            }

        # Cached prompt tokens counter
        counter_prompt_tokens_cached = self._counter_cls(
            name="vllm:prompt_tokens_cached",
            documentation="Number of cached prompt tokens (local + external).",
            labelnames=labelnames,
        )
        self.counter_prompt_tokens_cached = create_metric_per_engine(
            counter_prompt_tokens_cached, per_engine_labelvalues
        )

        counter_generation_tokens = self._counter_cls(
            name="vllm:generation_tokens",
            documentation="Number of generation tokens processed.",
            labelnames=labelnames,
        )
        self.counter_generation_tokens = create_metric_per_engine(
            counter_generation_tokens, per_engine_labelvalues
        )

        self.counter_request_success: dict[FinishReason, dict[int, Counter]] = {}
        counter_request_success_base = self._counter_cls(
            name="vllm:request_success",
            documentation="Count of successfully processed requests.",
            labelnames=labelnames + ["finished_reason"],
        )
        for reason in FinishReason:
            self.counter_request_success[reason] = {
                idx: counter_request_success_base.labels(
                    model_name, str(idx), str(reason)
                )
                for idx in engine_indexes
            }

        #
        # Histograms of counts
        #
        histogram_num_prompt_tokens_request = self._histogram_cls(
            name="vllm:request_prompt_tokens",
            documentation="Number of prefill tokens processed.",
            buckets=build_1_2_5_buckets(max_model_len),
            labelnames=labelnames,
        )
        self.histogram_num_prompt_tokens_request = create_metric_per_engine(
            histogram_num_prompt_tokens_request, per_engine_labelvalues
        )

        histogram_num_generation_tokens_request = self._histogram_cls(
            name="vllm:request_generation_tokens",
            documentation="Number of generation tokens processed.",
            buckets=build_1_2_5_buckets(max_model_len),
            labelnames=labelnames,
        )
        self.histogram_num_generation_tokens_request = create_metric_per_engine(
            histogram_num_generation_tokens_request, per_engine_labelvalues
        )

        # TODO: This metric might be incorrect in case of using multiple
        # api_server counts which uses prometheus mp.
        # See: https://github.com/vllm-project/vllm/pull/18053
        histogram_iteration_tokens = self._histogram_cls(
            name="vllm:iteration_tokens_total",
            documentation="Histogram of number of tokens per engine_step.",
            buckets=[1, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384],
            labelnames=labelnames,
        )
        self.histogram_iteration_tokens = create_metric_per_engine(
            histogram_iteration_tokens, per_engine_labelvalues
        )

        histogram_max_num_generation_tokens_request = self._histogram_cls(
            name="vllm:request_max_num_generation_tokens",
            documentation="Histogram of maximum number of requested generation tokens.",
            buckets=build_1_2_5_buckets(max_model_len),
            labelnames=labelnames,
        )
        self.histogram_max_num_generation_tokens_request = create_metric_per_engine(
            histogram_max_num_generation_tokens_request, per_engine_labelvalues
        )

        histogram_n_request = self._histogram_cls(
            name="vllm:request_params_n",
            documentation="Histogram of the n request parameter.",
            buckets=[1, 2, 5, 10, 20],
            labelnames=labelnames,
        )
        self.histogram_n_request = create_metric_per_engine(
            histogram_n_request, per_engine_labelvalues
        )

        histogram_max_tokens_request = self._histogram_cls(
            name="vllm:request_params_max_tokens",
            documentation="Histogram of the max_tokens request parameter.",
            buckets=build_1_2_5_buckets(max_model_len),
            labelnames=labelnames,
        )
        self.histogram_max_tokens_request = create_metric_per_engine(
            histogram_max_tokens_request, per_engine_labelvalues
        )

        #
        # Histogram of timing intervals
        #
        histogram_time_to_first_token = self._histogram_cls(
            name="vllm:time_to_first_token_seconds",
            documentation="Histogram of time to first token in seconds.",
            buckets=[
                0.001,
                0.005,
                0.01,
                0.02,
                0.04,
                0.06,
                0.08,
                0.1,
                0.25,
                0.5,
                0.75,
                1.0,
                2.5,
                5.0,
                7.5,
                10.0,
                20.0,
                40.0,
                80.0,
                160.0,
                640.0,
                2560.0,
            ],
            labelnames=labelnames,
        )
        self.histogram_time_to_first_token = create_metric_per_engine(
            histogram_time_to_first_token, per_engine_labelvalues
        )

        histogram_inter_token_latency = self._histogram_cls(
            name="vllm:inter_token_latency_seconds",
            documentation="Histogram of inter-token latency in seconds.",
            buckets=[
                0.01,
                0.025,
                0.05,
                0.075,
                0.1,
                0.15,
                0.2,
                0.3,
                0.4,
                0.5,
                0.75,
                1.0,
                2.5,
                5.0,
                7.5,
                10.0,
                20.0,
                40.0,
                80.0,
            ],
            labelnames=labelnames,
        )
        self.histogram_inter_token_latency = create_metric_per_engine(
            histogram_inter_token_latency, per_engine_labelvalues
        )

        histogram_request_time_per_output_token = self._histogram_cls(
            name="vllm:request_time_per_output_token_seconds",
            documentation="Histogram of time_per_output_token_seconds per request.",
            buckets=[
                0.01,
                0.025,
                0.05,
                0.075,
                0.1,
                0.15,
                0.2,
                0.3,
                0.4,
                0.5,
                0.75,
                1.0,
                2.5,
                5.0,
                7.5,
                10.0,
                20.0,
                40.0,
                80.0,
            ],
            labelnames=labelnames,
        )
        self.histogram_request_time_per_output_token = create_metric_per_engine(
            histogram_request_time_per_output_token, per_engine_labelvalues
        )

        request_latency_buckets = [
            0.3,
            0.5,
            0.8,
            1.0,
            1.5,
            2.0,
            2.5,
            5.0,
            10.0,
            15.0,
            20.0,
            30.0,
            40.0,
            50.0,
            60.0,
            120.0,
            240.0,
            480.0,
            960.0,
            1920.0,
            7680.0,
        ]
        histogram_e2e_time_request = self._histogram_cls(
            name="vllm:e2e_request_latency_seconds",
            documentation="Histogram of e2e request latency in seconds.",
            buckets=request_latency_buckets,
            labelnames=labelnames,
        )
        self.histogram_e2e_time_request = create_metric_per_engine(
            histogram_e2e_time_request, per_engine_labelvalues
        )

        histogram_queue_time_request = self._histogram_cls(
            name="vllm:request_queue_time_seconds",
            documentation="Histogram of time spent in WAITING phase for request.",
            buckets=request_latency_buckets,
            labelnames=labelnames,
        )
        self.histogram_queue_time_request = create_metric_per_engine(
            histogram_queue_time_request, per_engine_labelvalues
        )

        histogram_inference_time_request = self._histogram_cls(
            name="vllm:request_inference_time_seconds",
            documentation="Histogram of time spent in RUNNING phase for request.",
            buckets=request_latency_buckets,
            labelnames=labelnames,
        )
        self.histogram_inference_time_request = create_metric_per_engine(
            histogram_inference_time_request, per_engine_labelvalues
        )

        histogram_prefill_time_request = self._histogram_cls(
            name="vllm:request_prefill_time_seconds",
            documentation="Histogram of time spent in PREFILL phase for request.",
            buckets=request_latency_buckets,
            labelnames=labelnames,
        )
        self.histogram_prefill_time_request = create_metric_per_engine(
            histogram_prefill_time_request, per_engine_labelvalues
        )

        histogram_decode_time_request = self._histogram_cls(
            name="vllm:request_decode_time_seconds",
            documentation="Histogram of time spent in DECODE phase for request.",
            buckets=request_latency_buckets,
            labelnames=labelnames,
        )
        self.histogram_decode_time_request = create_metric_per_engine(
            histogram_decode_time_request, per_engine_labelvalues
        )

        histogram_prefill_kv_computed_request = self._histogram_cls(
            name="vllm:request_prefill_kv_computed_tokens",
            documentation=(
                "Histogram of new KV tokens computed during prefill "
                "(excluding cached tokens)."
            ),
            buckets=build_1_2_5_buckets(max_model_len),
            labelnames=labelnames,
        )
        self.histogram_prefill_kv_computed_request = create_metric_per_engine(
            histogram_prefill_kv_computed_request, per_engine_labelvalues
        )

        #
        # KV Cache residency metrics
        #
        if self.kv_cache_metrics_enabled:
            kv_cache_residency_buckets = [
                0.001,
                0.002,
                0.005,
                0.01,
                0.02,
                0.05,
                0.1,
                0.2,
                0.5,
                1,
                2,
                5,
                10,
                20,
                30,
                60,
                120,
                300,
                600,
                1200,
                1800,
            ]

            histogram_kv_block_lifetime = self._histogram_cls(
                name="vllm:kv_block_lifetime_seconds",
                documentation=(
                    "Histogram of KV cache block lifetime from allocation to eviction. "
                    "Sampled metrics (controlled by --kv-cache-metrics-sample)."
                ),
                buckets=kv_cache_residency_buckets,
                labelnames=labelnames,
            )
            self.histogram_kv_block_lifetime = create_metric_per_engine(
                histogram_kv_block_lifetime, per_engine_labelvalues
            )

            histogram_kv_block_idle_before_evict = self._histogram_cls(
                name="vllm:kv_block_idle_before_evict_seconds",
                documentation=(
                    "Histogram of idle time before KV cache block eviction. "
                    "Sampled metrics (controlled by --kv-cache-metrics-sample)."
                ),
                buckets=kv_cache_residency_buckets,
                labelnames=labelnames,
            )
            self.histogram_kv_block_idle_before_evict = create_metric_per_engine(
                histogram_kv_block_idle_before_evict, per_engine_labelvalues
            )

            histogram_kv_block_reuse_gap = self._histogram_cls(
                name="vllm:kv_block_reuse_gap_seconds",
                documentation=(
                    "Histogram of time gaps between consecutive KV cache block "
                    "accesses. Only the most recent accesses are recorded "
                    "(ring buffer). Sampled metrics (controlled by "
                    "--kv-cache-metrics-sample)."
                ),
                buckets=kv_cache_residency_buckets,
                labelnames=labelnames,
            )
            self.histogram_kv_block_reuse_gap = create_metric_per_engine(
                histogram_kv_block_reuse_gap, per_engine_labelvalues
            )
        else:
            self.histogram_kv_block_lifetime = {}
            self.histogram_kv_block_idle_before_evict = {}
            self.histogram_kv_block_reuse_gap = {}

        #
        # LoRA metrics
        #

        # TODO: This metric might be incorrect in case of using multiple
        # api_server counts which uses prometheus mp.
        self.gauge_lora_info: Gauge | None = None
        if vllm_config.lora_config is not None:
            if len(self.engine_indexes) > 1:
                logger.warning(
                    "vllm:lora_requests_info prometheus metrics may be "
                    "incorrect/misleading with data parallel deployments."
                )
            self.labelname_max_lora = "max_lora"
            self.labelname_waiting_lora_adapters = "waiting_lora_adapters"
            self.labelname_running_lora_adapters = "running_lora_adapters"
            self.max_lora = vllm_config.lora_config.max_loras
            self.gauge_lora_info = self._gauge_cls(
                name="vllm:lora_requests_info",
                documentation="Running stats on lora requests.",
                multiprocess_mode="sum",
                labelnames=[
                    self.labelname_max_lora,
                    self.labelname_waiting_lora_adapters,
                    self.labelname_running_lora_adapters,
                ],
            )