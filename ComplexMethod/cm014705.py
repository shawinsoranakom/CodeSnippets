def _compare_between(
        self, inputs, models, optimizers, assert_eq_kwargs=None, assert_step_dtype=None
    ):
        # why 7? iteration 7 is where we start to see differences for RAdam
        # params interacting with the small eps value, because that's right
        # after rho_t becomes greater than 5 in step 6.
        if assert_eq_kwargs is None:
            assert_eq_kwargs = {}
        kIterations = 7
        tracker = TensorTracker(assert_eq_kwargs)
        for i in range(kIterations):
            state, updated_params = [], []
            if not isinstance(inputs, list):
                inputs = [inputs, inputs]
            for input, model, optimizer in zip(inputs, models, optimizers):
                optimizer.zero_grad()

                if i == 3:
                    # Freeze a layer to test if the step of this layer in 'fused' or 'foreach'
                    # is same as the step in 'forloop'.
                    model[2].requires_grad_(False)
                if i == 5:
                    # Unfreeze the layer after 2 iters.
                    model[2].requires_grad_(True)

                # Test that step behaves as expected (a no-op) when grads are set to None
                if i != 2:
                    output = model(input)
                    loss = output.sum()
                    loss.backward()

                optimizer.step()
                state.append(optimizer.state)
                updated_params.append(model.parameters())

            og_state, new_state = state
            for og_p, new_p in zip(updated_params[0], updated_params[1]):
                tracker.add(og_p)
                tracker.pop_check_set(new_p, self)

                # check that optimizer states are the same
                og_p_state = og_state[og_p]
                new_p_state = new_state[new_p]
                if assert_step_dtype is not None:
                    if torch.is_tensor(og_p_state.get("step", None)):
                        self.assertEqual(og_p_state["step"].dtype, assert_step_dtype)
                    if torch.is_tensor(new_p_state.get("step", None)):
                        self.assertEqual(new_p_state["step"].dtype, assert_step_dtype)
                for k in og_p_state:
                    tracker.add(og_p_state[k])
                    tracker.pop_check_set(new_p_state[k], self)

            self.assertTrue(tracker.all_popped())