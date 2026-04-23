async def process_outputs_socket():
            try:
                while True:
                    frames = await output_socket.recv_multipart(copy=False)
                    resources.validate_alive(frames)
                    outputs: EngineCoreOutputs = decoder.decode(frames)
                    if outputs.utility_output:
                        if (
                            outputs.utility_output.call_id == EEP_NOTIFICATION_CALL_ID
                            and notification_callback_handler is not None
                        ):
                            assert _self_ref is not None
                            _self = _self_ref()
                            if not _self:
                                return
                            if outputs.utility_output.result is None:
                                continue
                            notification_data = outputs.utility_output.result.result
                            assert isinstance(notification_data, Sequence)
                            assert len(notification_data) == 2
                            asyncio.create_task(
                                notification_callback_handler(_self, notification_data)
                            )
                        else:
                            _process_utility_output(
                                outputs.utility_output, utility_results
                            )
                        continue

                    if output_handler is not None:
                        assert _self_ref is not None
                        _self = _self_ref()
                        if not _self:
                            # Client has been garbage collected, abort.
                            return
                        await output_handler(_self, outputs)

                    if outputs.outputs or outputs.scheduler_stats:
                        outputs_queue.put_nowait(outputs)
            except Exception as e:
                outputs_queue.put_nowait(e)
            except asyncio.CancelledError:
                outputs_queue.put_nowait(EngineDeadError())