def metadata(self, value):
        """
        Set the metadata. Update only the domains that are contained in the
        value dictionary.
        """
        # Loop through domains.
        for domain, metadata in value.items():
            # Set the domain to None for the default, otherwise encode.
            domain = None if domain == "DEFAULT" else domain.encode()
            # Set each metadata entry separately.
            for meta_name, meta_value in metadata.items():
                capi.set_ds_metadata_item(
                    self._ptr,
                    meta_name.encode(),
                    meta_value.encode() if meta_value else None,
                    domain,
                )