def _check_solver(solver, penalty, dual):
    if solver not in ["liblinear", "saga"] and penalty not in ("l2", None):
        raise ValueError(
            f"Solver {solver} supports only 'l2' or None penalties, got {penalty} "
            "penalty."
        )
    if solver != "liblinear" and dual:
        raise ValueError(f"Solver {solver} supports only dual=False, got dual={dual}")

    if penalty == "elasticnet" and solver != "saga":
        raise ValueError(
            f"Only 'saga' solver supports elasticnet penalty, got solver={solver}."
        )

    if solver == "liblinear" and penalty is None:
        # TODO(1.10): update message to remove "as well as penalty=None".
        raise ValueError(
            "C=np.inf as well as penalty=None is not supported for the liblinear solver"
        )

    return solver