def compare_predictions(pred_dict: dict, true_label: list) -> bool:
    """
    Compares each prediction against the corresponding true label.

    This function checks whether the predicted values match the true values for each
    metric. It sorts the true labels to ensure the comparison is made in the correct
    order. The function returns True if all predictions are accurate within a small
    tolerance for numerical values, or if string values match case-insensitively.

    Args:
        pred_dict (dict): A dictionary of predicted metrics and their values.
        true_label (list): A list of tuples containing true metrics and their values.

    Returns:
        bool: True if all predictions match the true labels, False otherwise.
    """
    sorted_true_label = sorted(true_label, key=lambda x: x[0])  # Sort true labels by metric name

    for metric, true_value in sorted_true_label:
        try:
            true_value = float(true_value)  # Attempt to convert the true value to float
        except ValueError:
            true_value = true_value.replace(",", "")  # Clean the true value if conversion fails

        # Check if the true value is numeric and compare with the prediction
        if isinstance(true_value, (int, float)) and (
            metric not in pred_dict or abs(pred_dict[metric] - true_value) > 1e-6
        ):
            return False  # Return False if the prediction is inaccurate

        # Check if the true value is a string and compare with the prediction
        if isinstance(true_value, str) and (
            metric not in pred_dict or str(pred_dict[metric]).lower() != str(true_value).lower()
        ):
            return False  # Return False if the string prediction does not match

    return True