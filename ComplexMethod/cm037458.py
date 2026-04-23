async def eep_process_engine_core_notification(
        self: "DPLBAsyncMPClient", notification_data: tuple[str, int]
    ):
        cache = self.eep_scaling_cache
        notification_type_str, dp_rank = notification_data
        try:
            notification_type = EEPNotificationType(notification_type_str)
        except ValueError as e:
            raise ValueError(
                f"Unknown EEP notification type: {notification_type_str}"
            ) from e

        if notification_type == EEPNotificationType.RECONFIGURE_FINISHED:
            from vllm.v1.engine import UtilityResult

            # NOTE(yongji): process a dummy UtilityOutput to resolve the future
            # awaited in _eep_wait_for_setup_switch_complete(), signaling that
            # all engine cores have completed reconfiguration.
            dummy_output = UtilityOutput(
                call_id=EEP_NOTIFICATION_CALL_ID, result=UtilityResult(None)
            )
            _process_utility_output(dummy_output, self.utility_results)
            return
        assert cache is not None
        if notification_type not in cache.pending_notifications:
            cache.pending_notifications[notification_type] = set()
        if dp_rank in cache.pending_notifications[notification_type]:
            raise ValueError(
                f"Duplicate notification {notification_type} from dp_rank {dp_rank}"
            )
        cache.pending_notifications[notification_type].add(dp_rank)
        if len(cache.pending_notifications[notification_type]) >= abs(
            cache.num_new_core_engines
        ):
            if notification_type == EEPNotificationType.SHUTDOWN_COMPLETE:
                assert isinstance(self.resources.engine_manager, CoreEngineActorManager)
                assert cache.num_new_core_engines < 0
                old_dp_size = len(cache.existing_core_engines)
                new_dp_size = old_dp_size + cache.num_new_core_engines
                self.resources.engine_manager.scale_down_elastic_ep(
                    old_dp_size, new_dp_size
                )
            else:
                await asyncio.gather(
                    *[
                        self._call_utility_async(
                            "eep_handle_engine_core_notification",
                            notification_type,
                            engine=engine,
                        )
                        for engine in cache.existing_core_engines
                    ]
                )
            cache.pending_notifications[notification_type] = set()
            if notification_type in [
                EEPNotificationType.SHUTDOWN_COMPLETE,
                EEPNotificationType.NEW_CORE_ENGINES_WEIGHTS_INIT_READY,
            ]:
                self.eep_scaling_cache = None