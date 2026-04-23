def _run_generation_loop(self) -> None:
        """Main processing loop running in the background thread."""
        try:
            # Try to retrieve an already initialized batch processor
            batch_processor = getattr(self, "batch_processor", None)
            # If the batch processor already exists, we just reset it for a new generation loop
            if isinstance(batch_processor, ContinuousBatchProcessor):
                batch_processor.reset()
            # Otherwise, we create a new batch processor
            else:
                batch_processor = self._create_batch_processor()

            # Start the generation loop
            self.batch_processor = batch_processor
            self.current_batch = 0

            # If using the async API, we bootstrap the first batch w/out update
            if batch_processor.use_async_batching:
                if not batch_processor.prepare_next_batch():
                    raise RuntimeError("Failed to bootstrap the first batch.")
                self._generation_step()
                self.current_batch += 1

            while (not self.stop_event.is_set()) or batch_processor.has_pending_requests():
                self._inner_generation_loop(batch_processor)
                self.current_batch += 1

            # In async mode, the last batch's results are still in flight - process them now
            # We need to switch back to the pair that has the last batch's D2H pending
            if isinstance(batch_processor.inputs_and_outputs, ContinuousBatchingAsyncIOs):
                batch_processor.inputs_and_outputs.current_pair = 1 - batch_processor.inputs_and_outputs.current_pair
                batch_processor.update_batch()

        except Exception as e:
            logger.error(f"Error in generation loop: {e}", exc_info=True)
            self._handle_critical_error(e, batch_processor)
        finally:
            logger.info("Generation loop finished.")