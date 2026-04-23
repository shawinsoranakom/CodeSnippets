def test_problem_types(self):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

        problem_types = [
            {"title": "multi_label_classification", "num_labels": 2, "dtype": torch.float},
            {"title": "single_label_classification", "num_labels": 1, "dtype": torch.long},
            {"title": "regression", "num_labels": 1, "dtype": torch.float},
        ]

        for model_class in self.all_model_classes:
            if (
                model_class.__name__
                not in [
                    *MODEL_FOR_IMAGE_CLASSIFICATION_MAPPING_NAMES.values(),
                ]
                or model_class.__name__ == "LevitForImageClassificationWithTeacher"
            ):
                continue

            for problem_type in problem_types:
                with self.subTest(msg=f"Testing {model_class} with {problem_type['title']}"):
                    config.problem_type = problem_type["title"]
                    config.num_labels = problem_type["num_labels"]

                    model = model_class(config)
                    model.to(torch_device)
                    model.train()

                    inputs = self._prepare_for_class(inputs_dict, model_class, return_labels=True)

                    if problem_type["num_labels"] > 1:
                        inputs["labels"] = inputs["labels"].unsqueeze(1).repeat(1, problem_type["num_labels"])

                    inputs["labels"] = inputs["labels"].to(problem_type["dtype"])

                    # This tests that we do not trigger the warning form PyTorch "Using a target size that is different
                    # to the input size. This will likely lead to incorrect results due to broadcasting. Please ensure
                    # they have the same size." which is a symptom something in wrong for the regression problem.
                    # See https://github.com/huggingface/transformers/issues/11780
                    with warnings.catch_warnings(record=True) as warning_list:
                        loss = model(**inputs).loss
                    for w in warning_list:
                        if "Using a target size that is different to the input size" in str(w.message):
                            raise ValueError(
                                f"Something is going wrong in the regression problem: intercepted {w.message}"
                            )

                    loss.backward()