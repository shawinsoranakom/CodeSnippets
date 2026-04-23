def main(all=False, models=None, check_only=False):
    if check_only:
        # Check all model cards for missing dates
        all_model_cards = get_all_model_cards()
        missing_dates = check_missing_dates(all_model_cards)

        # Check modified model cards for incorrect dates
        modified_cards = get_modified_cards()
        incorrect_dates = check_incorrect_dates(modified_cards)

        if missing_dates or incorrect_dates:
            problematic_cards = missing_dates + incorrect_dates
            model_names = [card.replace(".md", "") for card in problematic_cards]
            raise ValueError(
                f"Missing or incorrect dates in the following model cards: {' '.join(problematic_cards)}\n"
                f"Run `python utils/add_dates.py --models {' '.join(model_names)}` to fix them."
            )
        return

    # Determine which model cards to process
    if all:
        model_cards = get_all_model_cards()
    elif models:
        model_cards = models
    else:
        model_cards = get_modified_cards()
        if not model_cards:
            return

    insert_dates(model_cards)