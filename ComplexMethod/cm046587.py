def get_run_metrics(id: str) -> dict:
    """Return metric arrays for a run, using paired step arrays per metric."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT step, loss, learning_rate, grad_norm, eval_loss, epoch,
                   num_tokens, elapsed_seconds
            FROM training_metrics
            WHERE run_id = ?
            ORDER BY step
            """,
            (id,),
        ).fetchall()

        step_history: list[int] = []
        loss_history: list[float] = []
        loss_step_history: list[int] = []
        lr_history: list[float] = []
        lr_step_history: list[int] = []
        grad_norm_history: list[float] = []
        grad_norm_step_history: list[int] = []
        eval_loss_history: list[float] = []
        eval_step_history: list[int] = []
        final_epoch: float | None = None
        final_num_tokens: int | None = None

        for row in rows:
            step = row["step"]
            step_history.append(step)
            if step > 0 and row["loss"] is not None:
                loss_history.append(row["loss"])
                loss_step_history.append(step)
            if step > 0 and row["learning_rate"] is not None:
                lr_history.append(row["learning_rate"])
                lr_step_history.append(step)
            if step > 0 and row["grad_norm"] is not None:
                grad_norm_history.append(row["grad_norm"])
                grad_norm_step_history.append(step)
            if step > 0 and row["eval_loss"] is not None:
                eval_loss_history.append(row["eval_loss"])
                eval_step_history.append(step)
            if row["epoch"] is not None:
                final_epoch = row["epoch"]
            if row["num_tokens"] is not None:
                final_num_tokens = row["num_tokens"]

        return {
            "step_history": step_history,
            "loss_history": loss_history,
            "loss_step_history": loss_step_history,
            "lr_history": lr_history,
            "lr_step_history": lr_step_history,
            "grad_norm_history": grad_norm_history,
            "grad_norm_step_history": grad_norm_step_history,
            "eval_loss_history": eval_loss_history,
            "eval_step_history": eval_step_history,
            "final_epoch": final_epoch,
            "final_num_tokens": final_num_tokens,
        }
    finally:
        conn.close()