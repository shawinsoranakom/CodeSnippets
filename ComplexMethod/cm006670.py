async def list_files(self, flow_id: str) -> list[str]:
        """List all files in a specific flow directory.

        Args:
            flow_id: The identifier for the flow.

        Returns:
            List of file names in the flow directory.
        """
        if not isinstance(flow_id, str):
            flow_id = str(flow_id)

        folder_path = self.data_dir / flow_id
        if not await folder_path.exists() or not await folder_path.is_dir():
            await logger.awarning(f"Flow {flow_id} directory does not exist.")
            return []

        try:
            files = [p.name async for p in folder_path.iterdir() if await p.is_file()]
        except Exception:  # noqa: BLE001
            logger.exception(f"Error listing files in flow {flow_id}")
            return []
        else:
            await logger.ainfo(f"Listed {len(files)} files in flow {flow_id}.")
            return files