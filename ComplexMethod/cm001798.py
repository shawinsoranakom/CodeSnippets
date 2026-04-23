def test_capture_outputs_decorator(self):
        """Test that the decorator `capture_outputs` is not chained, and that only the base models use it.
        Also test that we can return all the needed outputs, i.e. the kwargs are passed and the custom `XXXOutput`
        classes accept the necessary keys.
        Chaining the calls to `capture_outputs` for the same output is not allowed because:
            1) useless - because the class above in the graph can simply reuse the already collected outputs
            2) dangerous - as outputs WILL be mixed up between the callers, i.e. the first call to the decorator will
                capture and return only the portion of the outputs that was not captured by the second `capture_outputs`
                call for that output.
        Note that chaining on different outputs (i.e. first call is set to capture "hidden_states" and 2nd to capture "attentions"
        is allowed, as we do not mix up outputs in this case.)
        """
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

        COUNTER = defaultdict(lambda: 0)
        origional_set = CompileableContextVar.set
        origional_reset = CompileableContextVar.reset

        # Every time we enter the `capture_outputs` decorator, we first call `set`, and then `reset`. So if we end
        # up calling `set` twice in a row before `reset`, it means we chained the calls to `capture_outputs` which is
        # an illegal practice
        def new_set(self, value):
            nonlocal COUNTER
            for k in value.keys():
                COUNTER[k] += 1
            if any(v > 1 for v in COUNTER.values()):
                raise ValueError("You're calling `capture_outputs` several time in a chain!")
            return origional_set(self, value)

        def new_reset(self, token):
            nonlocal COUNTER
            current_val = self.context_var.get()
            for k in current_val.keys():
                COUNTER[k] -= 1
            origional_reset(self, token)

        for model_class in self.all_model_classes:
            # Reset the counter in case one subtest fails and thus does not clean it up correctly
            COUNTER = defaultdict(lambda: 0)
            # Each individual model is a subtest
            with self.subTest(model_class.__name__):
                model = model_class(copy.deepcopy(config)).to(device=torch_device)
                model.eval()

                recordable_outputs = [
                    (module._can_record_outputs or {}).keys()
                    for module in model.modules()
                    if isinstance(module, PreTrainedModel)
                ]
                recordable_outputs = set().union(*recordable_outputs)
                # If we don't use the `capture_outputs` decorator, this test has no use
                if len(recordable_outputs) == 0:
                    self.skipTest("No usage of the `capture_outputs` decorator.")

                # Prepare inputs
                inputs = self._prepare_for_class(inputs_dict, model_class)
                return_all = {}
                # For attentions, any of those capturable are captured by `output_attentions`
                if any(x in recordable_outputs for x in ("attentions", "cross_attentions", "mask_decoder_attentions")):
                    return_all["output_attentions"] = True
                if "hidden_states" in recordable_outputs:
                    return_all["output_hidden_states"] = True
                if "router_logits" in recordable_outputs:
                    return_all["output_router_logits"] = True

                # Merge them (SwitchTransformers provides `output_router_logits` in `inputs` as well so we need to avoid
                # passing it twice)
                all_inputs = {**inputs, **return_all}

                # If we don't trigger the exception of the new set, then all good
                with patch.object(CompileableContextVar, "set", new=new_set):
                    with patch.object(CompileableContextVar, "reset", new=new_reset):
                        with torch.no_grad():
                            _ = model(**all_inputs)