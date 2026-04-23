async def update_step(
        self,
        task_id: str,
        step_id: str,
        status: Optional[str] = None,
        output: Optional[str] = None,
        additional_input: Optional[Dict[str, Any]] = None,
        additional_output: Optional[Dict[str, Any]] = None,
    ) -> Step:
        if self.debug_enabled:
            logger.debug(
                f"Updating step with task_id: {task_id} and step_id: {step_id}"
            )
        try:
            with self.Session() as session:
                if (
                    step := session.query(StepModel)
                    .filter_by(task_id=task_id, step_id=step_id)
                    .first()
                ):
                    if status is not None:
                        step.status = status
                    if additional_input is not None:
                        step.additional_input = additional_input
                    if output is not None:
                        step.output = output
                    if additional_output is not None:
                        step.additional_output = additional_output
                    session.commit()
                    return await self.get_step(task_id, step_id)
                else:
                    logger.error(
                        "Can't update non-existent Step with "
                        f"task_id: {task_id} and step_id: {step_id}"
                    )
                    raise NotFoundError("Step not found")
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error while getting step: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting step: {e}")
            raise