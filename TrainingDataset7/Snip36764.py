def validate_answer_to_universe(value):
    if value != 42:
        raise ValidationError(
            "This is not the answer to life, universe and everything!", code="not42"
        )