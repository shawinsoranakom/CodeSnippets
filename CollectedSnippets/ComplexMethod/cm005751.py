async def _run_get_execution(self, execution_id: str) -> tuple[str, str, Any | None]:
        try:
            result = await self.service.get_execution(user_id=self.user_id, execution_id=execution_id, db=self.db)
        except DeploymentNotFoundError as exc:
            return OUTCOME_NOT_FOUND, str(exc), None
        except ResourceConflictError as exc:
            return OUTCOME_CONFLICT, exc.message, None
        except InvalidContentError as exc:
            return OUTCOME_INVALID_CONTENT, exc.message, None
        except (InvalidDeploymentOperationError, InvalidDeploymentTypeError) as exc:
            return OUTCOME_INVALID_OPERATION, exc.message, None
        except DeploymentError as exc:
            return OUTCOME_FAILURE, exc.message, None
        except HTTPException as exc:
            return self._outcome_from_http_exception(exc), str(exc.detail), None
        except Exception as exc:  # noqa: BLE001
            return OUTCOME_FAILURE, str(exc), None
        else:
            return OUTCOME_SUCCESS, "execution_fetched", result