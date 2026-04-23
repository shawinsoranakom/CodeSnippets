def forward_fn(cg_mode: CUDAGraphMode) -> None:
                batch_descriptor = (
                    BatchDescriptor(num_tokens=num_tokens)
                    if cg_mode == CUDAGraphMode.PIECEWISE
                    else None
                )
                with set_forward_context(
                    attn_metadata if cg_mode != CUDAGraphMode.PIECEWISE else None,
                    self.vllm_config,
                    num_tokens=num_tokens,
                    cudagraph_runtime_mode=cg_mode,
                    num_tokens_across_dp=num_tokens_across_dp,
                    slot_mapping=slot_mappings,
                    batch_descriptor=batch_descriptor,
                ):
                    model_output = model(**model_inputs)

                if cg_mode == CUDAGraphMode.PIECEWISE:
                    # PW CUDA graph internally handles the model outputs.
                    # No need to keep track of the hidden states.
                    return None

                if self.is_last_pp_rank:
                    # Last PP rank (common case).
                    if self.use_aux_hidden_state_outputs:
                        hidden_states, aux_hidden_states = model_output
                    else:
                        hidden_states = model_output
                        aux_hidden_states = []
                    if self.hidden_states is None:
                        self.hidden_states = torch.empty_like(hidden_states)
                    self.hidden_states[:num_tokens] = hidden_states
                    if self.use_aux_hidden_state_outputs and not self.aux_hidden_states:
                        self.aux_hidden_states = [
                            torch.empty_like(x) for x in aux_hidden_states
                        ]
                    for i, aux in enumerate(aux_hidden_states):
                        self.aux_hidden_states[i][:num_tokens] = aux
                else:
                    # Non-last PP rank.
                    assert isinstance(model_output, IntermediateTensors)
                    intermediate_tensors = model_output
                    if self.intermediate_tensors is None:
                        self.intermediate_tensors = IntermediateTensors.empty_like(
                            intermediate_tensors
                        )
                    for k, v in intermediate_tensors.tensors.items():
                        self.intermediate_tensors[k][:num_tokens] = v