def run(self):
        """Generator that accepts prompts."""
        runner = self.runner
        mesh = runner.mesh
        max_len = runner.model.sequence_len
        batch_size = runner.batch_size
        params = self.params
        rngs = jax.random.split(jax.random.PRNGKey(1), batch_size)
        with mesh:
            memory = self.new_memory(params, batch_size, max_len)
            settings = SampleSettings(
                temperature=np.zeros((batch_size,), dtype=np.float32),
                nucleus_p=np.zeros((batch_size,), dtype=np.float32),
                mask=np.ones((batch_size, self.vocab_size), dtype=np.int32),
                active=np.zeros((batch_size), dtype=np.int32),
            )
            last_output = SampleOutput(
                token_id=np.zeros((batch_size, 1), dtype=np.int32),
                prob=np.zeros((batch_size, 1), dtype=jnp.bfloat16),
                top_k_token_ids=np.zeros((batch_size, TOP_K), dtype=np.int32),
                top_k_probs=np.zeros((batch_size, TOP_K), dtype=jnp.bfloat16),
            )

            prompt = np.array([300, 400, 500, 600, 600, 700, 800])

            new_settings = SampleSettings(
                temperature=np.float32(1),
                nucleus_p=np.float32(1),
                mask=np.ones((self.vocab_size,), dtype=np.int32),
                active=np.zeros((), dtype=np.int32),
            )
            rng_seed = np.uint64(1)

            for size in self.pad_sizes:
                if size > runner.model.sequence_len:
                    break
                logger.info("Precompile {}".format(size))
                prompt_len = len(prompt)
                prompt = pad_to_size(prompt, size)
                rngs, last_output, memory, settings = self.prefill_memory(
                    params,
                    rngs,
                    memory,
                    settings,
                    last_output,
                    prompt,
                    prompt_len,
                    rng_seed,
                    new_settings,
                    0,
                )
        with runner.mesh:
            logger.info("Compiling...")
            rngs, last_output, memory = self.sample_step(
                params, rngs, last_output, memory, settings
            )
            logger.info("Done compiling.")

        all_tokens = []
        free_slots = list(range(batch_size))
        requests = [None] * batch_size
        first_output = [None] * batch_size
        jax.tree_map(lambda x: x.copy_to_host_async(), last_output)
        prev_token = last_output
        step = 0
        total_num_tokens = 0
        total_num_sequences = 0
        with mesh:
            while True:
                while free_slots:
                    request: Optional[Request] = yield
                    tokens = self.tokenizer.encode(request.prompt)
                    temperature = request.temperature
                    nucleus_p = request.nucleus_p
                    rng_seed = request.rng_seed

                    i = free_slots.pop()
                    prompt = np.array(tokens, dtype=np.int32)
                    prompt_len = len(prompt)
                    prompt = pad_to_size(prompt, self.get_pad_bucket(prompt.shape[0]))
                    # All tokens are allowed.
                    mask = np.ones((self.vocab_size,), dtype=np.int32)

                    new_settings = SampleSettings(
                        temperature=np.float32(temperature),
                        nucleus_p=np.float32(nucleus_p),
                        mask=mask,
                        active=np.ones((), dtype=np.int32),
                    )
                    rng_seed = np.uint64(rng_seed)
                    rngs, last_output, memory, settings = self.prefill_memory(
                        params,
                        rngs,
                        memory,
                        settings,
                        last_output,
                        prompt,
                        prompt_len,
                        rng_seed,
                        new_settings,
                        i,
                    )
                    jax.tree_map(lambda x: x.copy_to_host_async(), last_output)
                    first_output[i] = last_output
                    requests[i] = request
                    total_num_sequences += 1

                rngs, last_output, memory = self.sample_step(
                    params, rngs, last_output, memory, settings
                )
                total_num_tokens += batch_size - len(free_slots)

                # prev_token should already be on the host.
                prev_token = jax.tree_map(np.array, prev_token)
                for i in range(batch_size):
                    if requests[i] is not None:
                        if first_output[i] is not None:
                            first_output_i = jax.tree_map(np.array, first_output[i])
                            all_tokens.append(int(first_output_i.token_id[i][0]))
                            first_output[i] = None
                            continue

                        all_tokens.append(int(prev_token.token_id[i][0]))
                        cont = len(all_tokens) < requests[i].max_len

                        if not cont:
                            output_str = self.tokenizer.decode(all_tokens)
                            requests[i] = None
                            free_slots.append(i)
                            all_tokens = []
                            settings = settings._replace(active=settings.active.at[i].set(0))
                            yield output_str

                jax.tree_map(lambda x: x.copy_to_host_async(), last_output)
                prev_token = last_output
                step += 1