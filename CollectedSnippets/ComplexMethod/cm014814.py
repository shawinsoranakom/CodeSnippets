def sample_inputs_generator():
                for sample_input in sample_inputs_func(device, dtype):
                    mask = sample_input.kwargs.get('mask')
                    if mask is None:
                        yield sample_input
                    else:
                        if layout == sample_input.input.layout:
                            yield sample_input
                        if layout != torch.strided:
                            sample_input_kwargs = sample_input.kwargs.copy()
                            sample_input_kwargs.update(mask=mask.to_dense())
                            yield SampleInput(sample_input.input.clone(),
                                              args=sample_input.args,
                                              kwargs=sample_input_kwargs)
                        if layout != torch.sparse_coo and op.supports_sparse:
                            sample_input_kwargs = sample_input.kwargs.copy()
                            sample_input_kwargs.update(mask=mask.to_sparse())
                            yield SampleInput(sample_input.input.clone(),
                                              args=sample_input.args,
                                              kwargs=sample_input_kwargs)
                        if layout != torch.sparse_csr and op.supports_sparse_csr and sample_input.input.ndim == 2:
                            sample_input_kwargs = sample_input.kwargs.copy()
                            sample_input_kwargs.update(mask=mask.to_sparse_csr())
                            yield SampleInput(sample_input.input.clone(),
                                              args=sample_input.args,
                                              kwargs=sample_input_kwargs)