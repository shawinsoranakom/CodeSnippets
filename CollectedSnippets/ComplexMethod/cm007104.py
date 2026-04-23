async def save_to_file(self) -> Message:
        """Save the input to a file and upload it, returning a confirmation message."""
        # Validate inputs
        if not self.file_name:
            msg = "File name must be provided."
            raise ValueError(msg)
        if not self._get_input_type():
            msg = "Input type is not set."
            raise ValueError(msg)

        # Get selected storage location
        storage_location = self._get_selected_storage_location()
        if not storage_location:
            msg = "Storage location must be selected."
            raise ValueError(msg)

        # Check if Local storage is disabled in cloud environment
        if storage_location == "Local" and is_astra_cloud_environment():
            msg = "Local storage is not available in cloud environment. Please use AWS or Google Drive."
            raise ValueError(msg)

        # Route to appropriate save method based on storage location
        if storage_location == "Local":
            return await self._save_to_local()
        if storage_location == "AWS":
            return await self._save_to_aws()
        if storage_location == "Google Drive":
            return await self._save_to_google_drive()
        msg = f"Unsupported storage location: {storage_location}"
        raise ValueError(msg)