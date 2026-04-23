def _create_version_model(
        self,
        function_name: str,
        region: str,
        account_id: str,
        description: str | None = None,
        revision_id: str | None = None,
        code_sha256: str | None = None,
        publish_to: FunctionVersionLatestPublished | None = None,
        is_active: bool = False,
    ) -> tuple[FunctionVersion, bool]:
        """
        Release a new version to the model if all restrictions are met.
        Restrictions:
          - CodeSha256, if provided, must equal the current latest version code hash
          - RevisionId, if provided, must equal the current latest version revision id
          - Some changes have been done to the latest version since last publish
        Will return a tuple of the version, and whether the version was published (True) or the latest available version was taken (False).
        This can happen if the latest version has not been changed since the last version publish, in this case the last version will be returned.

        :param function_name: Function name to be published
        :param region: Region of the function
        :param account_id: Account of the function
        :param description: new description of the version (will be the description of the function if missing)
        :param revision_id: Revision id, function will raise error if it does not match latest revision id
        :param code_sha256: Code sha256, function will raise error if it does not match latest code hash
        :return: Tuple of (published version, whether version was released or last released version returned, since nothing changed)
        """
        current_latest_version = get_function_version(
            function_name=function_name, qualifier="$LATEST", account_id=account_id, region=region
        )
        if revision_id and current_latest_version.config.revision_id != revision_id:
            raise PreconditionFailedException(
                "The Revision Id provided does not match the latest Revision Id. Call the GetFunction/GetAlias API to retrieve the latest Revision Id",
                Type="User",
            )

        # check if code hashes match if they are specified
        current_hash = (
            current_latest_version.config.code.code_sha256
            if current_latest_version.config.package_type == PackageType.Zip
            else current_latest_version.config.image.code_sha256
        )
        # if the code is a zip package and hot reloaded (hot reloading is currently only supported for zip packagetypes)
        # we cannot enforce the codesha256 check
        is_hot_reloaded_zip_package = (
            current_latest_version.config.package_type == PackageType.Zip
            and current_latest_version.config.code.is_hot_reloading()
        )
        if code_sha256 and current_hash != code_sha256 and not is_hot_reloaded_zip_package:
            raise InvalidParameterValueException(
                f"CodeSHA256 ({code_sha256}) is different from current CodeSHA256 in $LATEST ({current_hash}). Please try again with the CodeSHA256 in $LATEST.",
                Type="User",
            )

        state = lambda_stores[account_id][region]
        function = state.functions.get(function_name)
        changes = {}
        if description is not None:
            changes["description"] = description
        # TODO copy environment instead of restarting one, get rid of all the "Pending"s

        with function.lock:
            if function.next_version > 1 and (
                prev_version := function.versions.get(str(function.next_version - 1))
            ):
                if (
                    prev_version.config.internal_revision
                    == current_latest_version.config.internal_revision
                ):
                    return prev_version, False
            # TODO check if there was a change since last version
            if publish_to == FunctionVersionLatestPublished.LATEST_PUBLISHED:
                qualifier = "$LATEST.PUBLISHED"
            else:
                qualifier = str(function.next_version)
                function.next_version += 1
            new_id = VersionIdentifier(
                function_name=function_name,
                qualifier=qualifier,
                region=region,
                account=account_id,
            )

            if current_latest_version.config.capacity_provider_config:
                # for lambda managed functions, snap start is not supported
                snap_start = None
            else:
                apply_on = current_latest_version.config.snap_start["ApplyOn"]
                optimization_status = SnapStartOptimizationStatus.Off
                if apply_on == SnapStartApplyOn.PublishedVersions:
                    optimization_status = SnapStartOptimizationStatus.On
                snap_start = SnapStartResponse(
                    ApplyOn=apply_on,
                    OptimizationStatus=optimization_status,
                )

            last_update = None
            new_state = VersionState(
                state=State.Pending,
                code=StateReasonCode.Creating,
                reason="The function is being created.",
            )
            if publish_to == FunctionVersionLatestPublished.LATEST_PUBLISHED:
                last_update = UpdateStatus(
                    status=LastUpdateStatus.InProgress,
                    code="Updating",
                    reason="The function is being updated.",
                )
                if is_active:
                    new_state = VersionState(state=State.Active)
            new_version = dataclasses.replace(
                current_latest_version,
                config=dataclasses.replace(
                    current_latest_version.config,
                    last_update=last_update,
                    state=new_state,
                    snap_start=snap_start,
                    **changes,
                ),
                id=new_id,
            )
            function.versions[qualifier] = new_version
        return new_version, True