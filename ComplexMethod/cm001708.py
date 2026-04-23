def test_mismatching_num_image_tokens(self):
        """
        Tests that VLMs throw an error with explicit message saying what is wrong
        when number of images don't match number of image tokens in the text.
        Also we need to test multi-image cases when one prompt has multiple image tokens.
        """
        config, input_dict = self.model_tester.prepare_config_and_inputs_for_common()
        for model_class in self.all_model_classes:
            model = model_class(config).to(torch_device)
            model.eval()
            curr_input_dict = copy.deepcopy(input_dict)
            _ = model(**curr_input_dict)  # successful forward with no modifications

            # Test 1: remove one image but leave the image token in text
            curr_input_dict["pixel_values"] = curr_input_dict["pixel_values"][-1:, ...]
            if "image_sizes" in curr_input_dict:
                curr_input_dict["image_sizes"] = curr_input_dict["image_sizes"][-1:, ...]
            with self.assertRaises(ValueError):
                _ = model(**curr_input_dict)

            # Test 2: simulate multi-image case by concatenating inputs where each has exactly one image/image-token
            # First, take just the first item from each tensor
            curr_input_dict = {key: val[:1] for key, val in curr_input_dict.items()}

            # Double the batch size for all batch-dimension tensors except pixel_values
            # This simulates having 2 prompts (each with image tokens) but only 1 image
            batch_tensors_to_double = ["input_ids", "attention_mask", "token_type_ids"]
            for key in batch_tensors_to_double:
                if key in curr_input_dict and curr_input_dict[key] is not None:
                    curr_input_dict[key] = torch.cat([curr_input_dict[key], curr_input_dict[key]], dim=0)

            # one image and two image tokens raise an error
            with self.assertRaises(ValueError):
                _ = model(**curr_input_dict)

            # Test 3: two images and two image tokens don't raise an error
            curr_input_dict["pixel_values"] = torch.cat(
                [curr_input_dict["pixel_values"], curr_input_dict["pixel_values"]], dim=0
            )
            if "image_sizes" in curr_input_dict:
                curr_input_dict["image_sizes"] = torch.cat(
                    [curr_input_dict["image_sizes"], curr_input_dict["image_sizes"]], dim=0
                )
            _ = model(**curr_input_dict)