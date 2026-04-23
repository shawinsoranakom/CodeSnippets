def test_batching_equivalence(self, atol=1e-5, rtol=1e-5):
        """
        This test is overwritten because the model outputs do not contain only regressive values but also keypoint
        locations.
        Similarly to the problem discussed about SuperGlue implementation
        [here](https://github.com/huggingface/transformers/pull/29886#issuecomment-2482752787), the consequence of
        having different scores for matching, makes the maximum indices differ. These indices are being used to compute
        the keypoint coordinates. The keypoint coordinates, in the model outputs, are floating point tensors, so the
        original implementation of this test cover this case. But the resulting tensors may have differences exceeding
        the relative and absolute tolerance.
        Therefore, similarly to SuperGlue integration test, for the key "keypoints" in the model outputs, we check the
        number of differences in keypoint coordinates being less than a TODO given number
        """

        def recursive_check(batched_object, single_row_object, model_name, key):
            if isinstance(batched_object, (list, tuple)):
                for batched_object_value, single_row_object_value in zip(batched_object, single_row_object):
                    recursive_check(batched_object_value, single_row_object_value, model_name, key)
            elif isinstance(batched_object, dict):
                for batched_object_value, single_row_object_value in zip(
                    batched_object.values(), single_row_object.values()
                ):
                    recursive_check(batched_object_value, single_row_object_value, model_name, key)
            # do not compare returned loss (0-dim tensor) / codebook ids (int) / caching objects
            elif batched_object is None or not isinstance(batched_object, torch.Tensor):
                return
            elif batched_object.dim() == 0:
                return
            # do not compare int or bool outputs as they are mostly computed with max/argmax/topk methods which are
            # very sensitive to the inputs (e.g. tiny differences may give totally different results)
            elif not torch.is_floating_point(batched_object):
                return
            else:
                # indexing the first element does not always work
                # e.g. models that output similarity scores of size (N, M) would need to index [0, 0]
                slice_ids = tuple(slice(0, index) for index in single_row_object.shape)
                batched_row = batched_object[slice_ids]
                if key == "keypoints":
                    batched_row = torch.sum(batched_row, dim=-1)
                    single_row_object = torch.sum(single_row_object, dim=-1)
                    tolerance = 0.02 * single_row_object.shape[-1]
                    self.assertTrue(
                        torch.sum(~torch.isclose(batched_row, single_row_object, rtol=rtol, atol=atol)) < tolerance
                    )
                else:
                    self.assertFalse(
                        torch.isnan(batched_row).any(), f"Batched output has `nan` in {model_name} for key={key}"
                    )
                    self.assertFalse(
                        torch.isinf(batched_row).any(), f"Batched output has `inf` in {model_name} for key={key}"
                    )
                    self.assertFalse(
                        torch.isnan(single_row_object).any(),
                        f"Single row output has `nan` in {model_name} for key={key}",
                    )
                    self.assertFalse(
                        torch.isinf(single_row_object).any(),
                        f"Single row output has `inf` in {model_name} for key={key}",
                    )
                    try:
                        torch.testing.assert_close(batched_row, single_row_object, atol=atol, rtol=rtol)
                    except AssertionError as e:
                        msg = f"Batched and Single row outputs are not equal in {model_name} for key={key}.\n\n"
                        msg += str(e)
                        raise AssertionError(msg)

        config, batched_input = self.model_tester.prepare_config_and_inputs_for_common()
        set_config_for_less_flaky_test(config)

        for model_class in self.all_model_classes:
            config.output_hidden_states = True

            model_name = model_class.__name__
            if hasattr(self.model_tester, "prepare_config_and_inputs_for_model_class"):
                config, batched_input = self.model_tester.prepare_config_and_inputs_for_model_class(model_class)
            batched_input_prepared = self._prepare_for_class(batched_input, model_class)
            model = model_class(config).to(torch_device).eval()
            set_model_for_less_flaky_test(model)

            batch_size = self.model_tester.batch_size
            single_row_input = {}
            for key, value in batched_input_prepared.items():
                if isinstance(value, torch.Tensor) and value.shape[0] % batch_size == 0:
                    # e.g. musicgen has inputs of size (bs*codebooks). in most cases value.shape[0] == batch_size
                    single_batch_shape = value.shape[0] // batch_size
                    single_row_input[key] = value[:single_batch_shape]
                else:
                    single_row_input[key] = value

            with torch.no_grad():
                model_batched_output = model(**batched_input_prepared)
                model_row_output = model(**single_row_input)

            if isinstance(model_batched_output, torch.Tensor):
                model_batched_output = {"model_output": model_batched_output}
                model_row_output = {"model_output": model_row_output}

            for key in model_batched_output:
                # DETR starts from zero-init queries to decoder, leading to cos_similarity = `nan`
                if hasattr(self, "zero_init_hidden_state") and "decoder_hidden_states" in key:
                    model_batched_output[key] = model_batched_output[key][1:]
                    model_row_output[key] = model_row_output[key][1:]
                recursive_check(model_batched_output[key], model_row_output[key], model_name, key)