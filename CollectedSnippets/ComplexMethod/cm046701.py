def _handle_event(self, event: dict) -> None:
        """Apply a subprocess event to local state.

        State updates happen inside self._lock; DB I/O happens after
        releasing it so status-polling API endpoints are never blocked
        by slow SQLite writes.
        """
        etype = event.get("type")
        db_action: Optional[str] = None
        db_action_kwargs: dict = {}

        with self._lock:
            if etype == "progress":
                self._progress.step = event.get("step", self._progress.step)
                self._progress.epoch = event.get("epoch", self._progress.epoch)
                # loss/lr are sanitized below; update progress after coercion
                _raw_loss = event.get("loss")
                _raw_lr = event.get("learning_rate")
                try:
                    _safe_loss = float(_raw_loss) if _raw_loss is not None else None
                except (TypeError, ValueError):
                    logger.debug("Could not convert loss to float: %s", _raw_loss)
                    _safe_loss = None
                if _safe_loss is not None and not math.isfinite(_safe_loss):
                    _safe_loss = None
                try:
                    _safe_lr = float(_raw_lr) if _raw_lr is not None else None
                except (TypeError, ValueError):
                    logger.debug(
                        "Could not convert learning_rate to float: %s", _raw_lr
                    )
                    _safe_lr = None
                if _safe_lr is not None and not math.isfinite(_safe_lr):
                    _safe_lr = None
                if _safe_loss is not None:
                    self._progress.loss = _safe_loss
                if _safe_lr is not None:
                    self._progress.learning_rate = _safe_lr
                self._progress.total_steps = event.get(
                    "total_steps", self._progress.total_steps
                )
                self._progress.elapsed_seconds = event.get("elapsed_seconds")
                self._progress.eta_seconds = event.get("eta_seconds")
                self._progress.grad_norm = event.get("grad_norm")
                self._progress.num_tokens = event.get("num_tokens")
                self._progress.eval_loss = event.get("eval_loss")
                self._progress.is_training = True
                status = event.get("status_message", "")
                if status:
                    self._progress.status_message = status

                # Update metric histories — reuse sanitized values from above
                step = event.get("step", 0)
                loss = _safe_loss
                lr = _safe_lr
                if step > 0 and loss is not None:
                    self.loss_history.append(loss)
                    self.lr_history.append(lr if lr is not None else 0.0)
                    self.step_history.append(step)

                grad_norm = event.get("grad_norm")
                gn = None
                if grad_norm is not None:
                    try:
                        gn = float(grad_norm)
                    except (TypeError, ValueError):
                        gn = None
                    if step > 0 and gn is not None and math.isfinite(gn):
                        self.grad_norm_history.append(gn)
                        self.grad_norm_step_history.append(step)
                    else:
                        gn = None

                eval_loss = event.get("eval_loss")
                if eval_loss is not None:
                    try:
                        eval_loss = float(eval_loss)
                    except (TypeError, ValueError):
                        logger.debug(
                            "Could not convert eval_loss to float: %s", eval_loss
                        )
                        eval_loss = None
                    if step > 0 and eval_loss is not None and math.isfinite(eval_loss):
                        self.eval_loss_history.append(eval_loss)
                        self.eval_step_history.append(step)
                        self.eval_enabled = True
                    else:
                        eval_loss = None

                # Buffer metric for DB flush (loss/lr already sanitized above)
                self._metric_buffer.append(
                    {
                        "step": step,
                        "loss": loss,
                        "learning_rate": lr,
                        "grad_norm": gn,
                        "eval_loss": eval_loss,
                        "epoch": event.get("epoch"),
                        "num_tokens": event.get("num_tokens"),
                        "elapsed_seconds": event.get("elapsed_seconds"),
                    }
                )

                # Decide which DB action to take after releasing the lock
                if not self._db_run_created and self.current_job_id and self._db_config:
                    db_action = "create_run"
                    db_action_kwargs = {
                        "job_id": self.current_job_id,
                        "model_name": self._db_config["model_name"],
                        "dataset_name": self._db_config.get("hf_dataset")
                        or next(
                            iter(self._db_config.get("local_datasets") or []), "unknown"
                        ),
                        "config_json": _json.dumps(self._db_config),
                        "started_at": self._db_started_at
                        or datetime.now(timezone.utc).isoformat(),
                        "total_steps": event.get("total_steps"),
                    }
                elif (
                    event.get("total_steps")
                    and self._db_run_created
                    and not self._db_total_steps_set
                ):
                    db_action = "update_total_steps"
                    db_action_kwargs = {
                        "job_id": self.current_job_id,
                        "total_steps": event["total_steps"],
                    }
                elif len(self._metric_buffer) >= self.FLUSH_THRESHOLD:
                    db_action = "flush"

            elif etype == "eval_configured":
                self.eval_enabled = True

            elif etype == "status":
                self._progress.status_message = event.get("message", "")
                self._progress.is_training = True

            elif etype == "complete":
                self._progress.is_training = False
                self._progress.is_completed = True
                self._output_dir = event.get("output_dir")
                msg = event.get("status_message", "Training completed")
                self._progress.status_message = msg
                if not self._db_run_created and self.current_job_id and self._db_config:
                    db_action = "create_and_finalize"
                else:
                    db_action = "finalize"
                db_action_kwargs = {
                    "status": "stopped" if self._should_stop else "completed",
                    "output_dir": self._output_dir,
                }

            elif etype == "error":
                self._progress.is_training = False
                self._progress.error = event.get("error", "Unknown error")
                logger.error("Training error: %s", event.get("error"))
                stack = event.get("stack", "")
                if stack:
                    logger.error("Stack trace:\n%s", stack)
                if not self._db_run_created and self.current_job_id and self._db_config:
                    db_action = "create_and_finalize"
                else:
                    db_action = "finalize"
                db_action_kwargs = {
                    "status": "stopped" if self._should_stop else "error",
                    "error_message": event.get("error", "Unknown error"),
                }

        # --- DB I/O outside the lock ---
        if db_action == "create_run":
            try:
                from storage.studio_db import create_run

                create_run(
                    id = db_action_kwargs["job_id"],
                    model_name = db_action_kwargs["model_name"],
                    dataset_name = db_action_kwargs["dataset_name"],
                    config_json = db_action_kwargs["config_json"],
                    started_at = db_action_kwargs["started_at"],
                    total_steps = db_action_kwargs["total_steps"],
                )
                self._db_run_created = True
                if db_action_kwargs["total_steps"]:
                    self._db_total_steps_set = True
            except Exception:
                logger.warning("Failed to create DB run record", exc_info = True)
        elif db_action == "create_and_finalize":
            self._ensure_db_run_created()
            self._finalize_run_in_db(**db_action_kwargs)
        elif db_action == "update_total_steps":
            try:
                from storage.studio_db import update_run_total_steps

                update_run_total_steps(
                    db_action_kwargs["job_id"], db_action_kwargs["total_steps"]
                )
                self._db_total_steps_set = True
            except Exception:
                logger.warning("Failed to update total_steps in DB", exc_info = True)
        elif db_action == "flush":
            self._flush_metrics_to_db()
        elif db_action == "finalize":
            self._finalize_run_in_db(**db_action_kwargs)