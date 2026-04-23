def execute_model_ray(
            self,
            execute_model_input: tuple["SchedulerOutput", "GrammarOutput"]
            | tuple["SchedulerOutput", "GrammarOutput", "IntermediateTensors"],
        ) -> Union[
            "ModelRunnerOutput",
            tuple["SchedulerOutput", "GrammarOutput", "IntermediateTensors"],
        ]:
            # This method is used by Ray Compiled Graph to execute the model,
            # and it needs a special logic of self.setup_device_if_necessary()
            self.setup_device_if_necessary()
            assert self.worker is not None, "Worker is not initialized"
            if len(execute_model_input) == 3:
                scheduler_output, grammar_output, intermediate_tensors = (
                    execute_model_input
                )
            else:
                scheduler_output, grammar_output = execute_model_input
                intermediate_tensors = None
            assert self.worker.model_runner is not None
            output = self.worker.model_runner.execute_model(
                scheduler_output, intermediate_tensors
            )
            if self._is_intermediate_tensors(output):
                if (
                    self.worker.model_runner.supports_mm_inputs
                    and get_pp_group().is_first_rank
                ):
                    # Strip mm_features before Ray forwards it to the next PP Stage.
                    # PP Stage>0 only needs the intermediate tensors,
                    # not preprocessed multimodal data.

                    # scheduled_new_reqs is a required field of SchedulerOutput,
                    # so accessing it directly will raise AttributeError if missing.
                    for req in scheduler_output.scheduled_new_reqs:
                        req.mm_features = []
                return scheduler_output, grammar_output, output

            if isinstance(output, AsyncModelRunnerOutput):
                output = output.get_output()
            if not self._is_last_rank():
                # Case where there are no scheduled requests
                # but may still be finished requests.
                assert not output or not output.req_ids
                output = scheduler_output, grammar_output, None
            elif output is None:
                output = self.worker.model_runner.sample_tokens(grammar_output)
                # Ensure outputs crossing Ray compiled DAG are serializable.
                # AsyncModelRunnerOutput holds CUDA events and cannot be
                # pickled.
                if isinstance(output, AsyncModelRunnerOutput):
                    output = output.get_output()
            return output