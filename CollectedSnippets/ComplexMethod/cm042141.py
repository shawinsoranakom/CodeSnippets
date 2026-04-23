def single_eval(self, id: str, prediction: str) -> dict:
        """
        Evaluate the prediction against the true label for a single question.
        just using in eval_all

        Args:
            id (str): The identifier for the question.
            prediction (str): The prediction string to evaluate.

        Returns:
            dict: A dictionary indicating the correctness of each metric.
        """
        true_label = self.get_answer(id)["common_answers"]  # Retrieve the true label for the question
        prediction = prediction.replace("{", "").replace("}", "").replace("'", "")  # Clean the prediction string
        pred_dict = parse_prediction(prediction)  # Parse the prediction into a dictionary

        # Initialize the correctness dictionary with False values for each metric
        correctness = {metric: False for metric, _ in true_label}

        # Check each metric's prediction against the true label
        for metric, true_value in true_label:
            try:
                true_value = float(true_value)  # Attempt to convert the true value to float
            except ValueError:
                true_value = true_value.replace(",", "")  # Handle non-numeric values

            if metric in pred_dict:
                # Consider the prediction correct if it's within a small tolerance
                if (
                    isinstance(true_value, (int, float))
                    and isinstance(pred_dict[metric], (int, float))
                    and abs(pred_dict[metric] - true_value) < 1e-6
                ):
                    correctness[metric] = True  # Mark as correct if within tolerance

                if isinstance(true_value, str) and (
                    metric not in pred_dict or str(pred_dict[metric]).lower() != str(true_value).lower()
                ):
                    correctness[metric] = True  # Mark as correct for string comparison

        return correctness