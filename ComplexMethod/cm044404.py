def _run_training_cycle(self, trainer: Trainer) -> None:
        """Perform the training cycle.

        Handles the background training, updating previews/time-lapse on each save interval,
        and saving the model.

        Parameters
        ----------
        trainer
            The requested model trainer plugin
        """
        logger.debug("[Train] Running Training Cycle")
        update_preview_images = False
        if self._args.write_image or self._args.redirect_gui or self._args.preview:
            display_func: Callable | None = self._show
        else:
            display_func = None

        for iteration in range(1, self._args.iterations + 1):
            logger.trace("[Train] Training iteration: %s", iteration)  # type:ignore
            save_iteration = iteration % self._args.save_interval == 0 or iteration == 1
            gui_triggers = self._process_gui_triggers()

            if self._preview.should_toggle_mask or gui_triggers["mask"]:
                trainer.toggle_mask()
                update_preview_images = True

            if self._preview.should_refresh or gui_triggers["refresh"] or update_preview_images:
                viewer = display_func
                update_preview_images = False
            else:
                viewer = None

            trainer.train_one_step(viewer, self._timelapse and save_iteration)

            if viewer is not None and not save_iteration:
                # Ugly spam but required by GUI to know to update window
                print("\x1b[2K", end="\r")  # Clear last line
                logger.info("[Preview Updated]")

            if self._stop:
                logger.debug("[Train] Stop received. Terminating")
                break

            if save_iteration or self._save_now:
                logger.debug("[Train] Saving (save_iterations: %s, save_now: %s) Iteration: "
                             "(iteration: %s)", save_iteration, self._save_now, iteration)
                trainer.save(is_exit=False)
                self._save_now = False
                update_preview_images = True

        logger.debug("[Train] Training cycle complete")
        trainer.save(is_exit=True)
        self._stop = True