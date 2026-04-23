async def async_upload_backup(
        self,
        *,
        open_stream: Callable[[], Coroutine[Any, Any, AsyncIterator[bytes]]],
        backup: AgentBackup,
        on_progress: OnProgressCallback,
        **kwargs: Any,
    ) -> None:
        """Upload a backup.

        :param open_stream: A function returning an async iterator that yields bytes.
        :param backup: Metadata about the backup that should be uploaded.
        """
        if not backup.protected:
            raise BackupAgentError("Cloud backups must be protected")
        if self._cloud.subscription_expired:
            raise BackupAgentError("Cloud subscription has expired")

        size = backup.size
        try:
            base64md5hash = await calculate_b64md5(open_stream, size)
        except FilesError as err:
            raise BackupAgentError(err) from err
        filename = f"{self._cloud.client.prefs.instance_id}.tar"
        metadata = backup.as_dict()

        tries = 1
        while tries <= _RETRY_LIMIT:
            try:
                await self._cloud.files.upload(
                    storage_type=StorageType.BACKUP,
                    open_stream=open_stream,
                    filename=filename,
                    base64md5hash=base64md5hash,
                    metadata=metadata,
                    size=size,
                    on_progress=on_progress,
                )
                break
            except CloudApiNonRetryableError as err:
                if err.code == "NC-SH-FH-03":
                    raise BackupAgentError(
                        translation_domain=DOMAIN,
                        translation_key="backup_size_too_large",
                        translation_placeholders={
                            "size": str(round(size / (1024**3), 2))
                        },
                    ) from err
                raise BackupAgentError(f"Failed to upload backup {err}") from err
            except CloudError as err:
                if (
                    isinstance(err, CloudApiError)
                    and isinstance(err.orig_exc, ClientResponseError)
                    and err.orig_exc.status == HTTPStatus.FORBIDDEN
                    and self._cloud.subscription_expired
                ):
                    raise BackupAgentError("Cloud subscription has expired") from err
                if tries == _RETRY_LIMIT:
                    raise BackupAgentError(f"Failed to upload backup {err}") from err
                tries += 1
                retry_timer = random.randint(_RETRY_SECONDS_MIN, _RETRY_SECONDS_MAX)
                _LOGGER.info(
                    "Failed to upload backup, retrying (%s/%s) in %ss: %s",
                    tries,
                    _RETRY_LIMIT,
                    retry_timer,
                    err,
                )
                await asyncio.sleep(retry_timer)