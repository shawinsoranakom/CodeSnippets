async def event_generator():
        backend = get_training_backend()
        job_id: str = getattr(backend, "current_job_id", "") or ""

        # ── Helpers ──────────────────────────────────────────────
        def build_progress(
            step: int,
            loss: Optional[float],
            learning_rate: Optional[float],
            total_steps: int,
            epoch: Optional[float] = None,
            progress: Optional[Any] = None,
            grad_norm_override: Optional[float] = None,
            eval_loss_override: Optional[float] = None,
        ) -> TrainingProgress:
            total = max(total_steps, 0)
            if step < 0 or total == 0:
                progress_percent = 0.0
            else:
                progress_percent = (
                    float(step) / float(total) * 100.0 if total > 0 else 0.0
                )

            # Get actual values from progress object if available
            elapsed_seconds = (
                getattr(progress, "elapsed_seconds", None) if progress else None
            )
            eta_seconds = getattr(progress, "eta_seconds", None) if progress else None
            grad_norm = grad_norm_override
            if grad_norm is None and progress:
                grad_norm = getattr(progress, "grad_norm", None)
            num_tokens = getattr(progress, "num_tokens", None) if progress else None
            eval_loss = eval_loss_override
            if eval_loss is None and progress:
                eval_loss = getattr(progress, "eval_loss", None)

            return TrainingProgress(
                job_id = job_id,
                step = step,
                total_steps = total,
                loss = loss,
                learning_rate = learning_rate,
                progress_percent = progress_percent,
                epoch = epoch,
                elapsed_seconds = elapsed_seconds,
                eta_seconds = eta_seconds,
                grad_norm = grad_norm,
                num_tokens = num_tokens,
                eval_loss = eval_loss,
            )

        def format_sse(
            data: str,
            event: str = "progress",
            event_id: Optional[int] = None,
        ) -> str:
            """Format a single SSE message with id/event/data fields."""
            lines = []
            if event_id is not None:
                lines.append(f"id: {event_id}")
            lines.append(f"event: {event}")
            lines.append(f"data: {data}")
            lines.append("")  # trailing blank line
            lines.append("")  # double newline terminates the event
            return "\n".join(lines)

        # ── Retry directive ──────────────────────────────────────
        # Tell the browser to reconnect after 3 seconds if the connection drops
        yield "retry: 3000\n\n"

        # ── Replay missed steps on reconnect ─────────────────────
        if resume_from_step is not None and backend.step_history:
            replayed = 0
            grad_norm_by_step = {
                step_val: grad_val
                for step_val, grad_val in zip(
                    getattr(backend, "grad_norm_step_history", []),
                    getattr(backend, "grad_norm_history", []),
                )
            }
            for i, step_val in enumerate(backend.step_history):
                if step_val > resume_from_step:
                    loss_val = (
                        backend.loss_history[i]
                        if i < len(backend.loss_history)
                        else None
                    )
                    lr_val = (
                        backend.lr_history[i] if i < len(backend.lr_history) else None
                    )
                    tp_replay = getattr(
                        getattr(backend, "trainer", None), "training_progress", None
                    )
                    total_replay = (
                        getattr(tp_replay, "total_steps", step_val)
                        if tp_replay
                        else step_val
                    )
                    epoch_replay = (
                        getattr(tp_replay, "epoch", None) if tp_replay else None
                    )
                    payload = build_progress(
                        step_val,
                        loss_val,
                        lr_val,
                        total_replay,
                        epoch_replay,
                        progress = tp_replay,
                        grad_norm_override = grad_norm_by_step.get(step_val),
                    )
                    yield format_sse(
                        payload.model_dump_json(), event = "progress", event_id = step_val
                    )
                    replayed += 1
            if replayed:
                logger.info(f"SSE reconnect: replayed {replayed} missed steps")

        # ── Initial status (only on fresh connections) ───────────
        if resume_from_step is None:
            is_active = backend.is_training_active()
            tp = getattr(getattr(backend, "trainer", None), "training_progress", None)
            initial_total_steps = getattr(tp, "total_steps", 0) if tp else 0
            initial_epoch = getattr(tp, "epoch", None) if tp else None

            initial_progress = build_progress(
                step = 0,
                loss = None,
                learning_rate = None,
                total_steps = initial_total_steps,
                epoch = initial_epoch,
                progress = tp,
            )
            yield format_sse(
                initial_progress.model_dump_json(), event = "progress", event_id = 0
            )

            # If not active, send final state and exit
            if not is_active:
                if backend.step_history:
                    final_step = backend.step_history[-1]
                    final_loss = (
                        backend.loss_history[-1] if backend.loss_history else None
                    )
                    final_lr = backend.lr_history[-1] if backend.lr_history else None
                    final_total_steps = (
                        getattr(tp, "total_steps", final_step) if tp else final_step
                    )
                    final_epoch = getattr(tp, "epoch", None) if tp else None
                    payload = build_progress(
                        final_step,
                        final_loss,
                        final_lr,
                        final_total_steps,
                        final_epoch,
                        progress = tp,
                    )
                    yield format_sse(
                        payload.model_dump_json(), event = "complete", event_id = final_step
                    )
                else:
                    yield format_sse(
                        build_progress(
                            -1, None, None, 0, progress = tp
                        ).model_dump_json(),
                        event = "complete",
                        event_id = 0,
                    )
                return

        # ── Live polling loop ────────────────────────────────────
        last_step = resume_from_step if resume_from_step is not None else -1
        no_update_count = 0
        max_no_updates = (
            1800  # Timeout after 30 minutes (large models need time for compilation)
        )

        while backend.is_training_active():
            try:
                if backend.step_history:
                    current_step = backend.step_history[-1]
                    current_loss = (
                        backend.loss_history[-1] if backend.loss_history else None
                    )
                    current_lr = backend.lr_history[-1] if backend.lr_history else None
                    tp_inner = getattr(
                        getattr(backend, "trainer", None), "training_progress", None
                    )
                    current_total_steps = (
                        getattr(tp_inner, "total_steps", current_step)
                        if tp_inner
                        else current_step
                    )
                    current_epoch = (
                        getattr(tp_inner, "epoch", None) if tp_inner else None
                    )

                    # Only send if step changed
                    if current_step != last_step:
                        progress_payload = build_progress(
                            current_step,
                            current_loss,
                            current_lr,
                            current_total_steps,
                            current_epoch,
                            progress = tp_inner,
                        )
                        yield format_sse(
                            progress_payload.model_dump_json(),
                            event = "progress",
                            event_id = current_step,
                        )
                        last_step = current_step
                        no_update_count = 0
                    else:
                        no_update_count += 1
                        # Send heartbeat every 10 seconds
                        if no_update_count % 10 == 0:
                            heartbeat_payload = build_progress(
                                current_step,
                                current_loss,
                                current_lr,
                                current_total_steps,
                                current_epoch,
                                progress = tp_inner,
                            )
                            yield format_sse(
                                heartbeat_payload.model_dump_json(),
                                event = "heartbeat",
                                event_id = current_step,
                            )
                else:
                    # No steps yet, but training is active (model loading, etc.)
                    no_update_count += 1
                    if no_update_count % 5 == 0:
                        # Pull total_steps and status from trainer so
                        # the frontend can show "Tokenizing…" etc.
                        tp_prep = getattr(
                            getattr(backend, "trainer", None),
                            "training_progress",
                            None,
                        )
                        prep_total = (
                            getattr(tp_prep, "total_steps", 0) if tp_prep else 0
                        )
                        preparing_payload = build_progress(
                            0,
                            None,
                            None,
                            prep_total,
                            progress = tp_prep,
                        )
                        yield format_sse(
                            preparing_payload.model_dump_json(),
                            event = "heartbeat",
                            event_id = 0,
                        )

                # Timeout check
                if no_update_count > max_no_updates:
                    logger.warning("Progress stream timeout - no updates received")
                    tp_timeout = getattr(
                        getattr(backend, "trainer", None), "training_progress", None
                    )
                    timeout_payload = build_progress(
                        last_step, None, None, 0, progress = tp_timeout
                    )
                    yield format_sse(
                        timeout_payload.model_dump_json(),
                        event = "error",
                        event_id = last_step if last_step >= 0 else 0,
                    )
                    break

                await asyncio.sleep(1)  # Poll every second

            except Exception as e:
                logger.error(f"Error in progress stream: {e}", exc_info = True)
                tp_error = getattr(
                    getattr(backend, "trainer", None), "training_progress", None
                )
                error_payload = build_progress(0, None, None, 0, progress = tp_error)
                yield format_sse(
                    error_payload.model_dump_json(),
                    event = "error",
                    event_id = last_step if last_step >= 0 else 0,
                )
                break

        # ── Final "complete" event ───────────────────────────────
        final_step = backend.step_history[-1] if backend.step_history else last_step
        final_loss = backend.loss_history[-1] if backend.loss_history else None
        final_lr = backend.lr_history[-1] if backend.lr_history else None
        final_tp = getattr(getattr(backend, "trainer", None), "training_progress", None)
        final_total_steps = (
            getattr(final_tp, "total_steps", final_step) if final_tp else final_step
        )
        final_epoch = getattr(final_tp, "epoch", None) if final_tp else None
        final_payload = build_progress(
            final_step,
            final_loss,
            final_lr,
            final_total_steps,
            final_epoch,
            progress = final_tp,
        )
        yield format_sse(
            final_payload.model_dump_json(),
            event = "complete",
            event_id = final_step if final_step >= 0 else 0,
        )