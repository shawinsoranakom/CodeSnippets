async def _run_update(
        self,
        deployment_id: str,
        payload: DeploymentUpdate,
        *,
        inject: dict[str, dict[str, Any]] | None = None,
    ) -> tuple[str, str, Any | None]:
        originals: list[tuple[Any, str, Any]] = []
        try:
            if inject:
                self._apply_injections(inject, originals)
            result = await self.service.update(
                user_id=self.user_id,
                deployment_id=deployment_id,
                payload=payload,
                db=self.db,
            )
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
            self.created_config_ids.update(self._extract_update_created_app_ids(result))
            return OUTCOME_SUCCESS, "updated", result
        finally:
            for target, attr_name, original in originals:
                setattr(target, attr_name, original)