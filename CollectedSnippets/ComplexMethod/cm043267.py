def _decode_cert_data(data: Any) -> Any:
        """Helper method to decode bytes in certificate data."""
        if isinstance(data, bytes):
            try:
                # Try UTF-8 first, fallback to latin-1 for arbitrary bytes
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return data.decode("latin-1") # Or handle as needed, maybe hex representation
        elif isinstance(data, dict):
            return {
                (
                    k.decode("utf-8") if isinstance(k, bytes) else k
                ): SSLCertificate._decode_cert_data(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [SSLCertificate._decode_cert_data(item) for item in data]
        return data