def _get_storage_info(self) -> dict:
        """
        Get storage space usage information.

        Returns:
            dict: Storage information with used and total space
        """
        try:
            # Get database size
            result = self.client.perform_raw_text_sql(
                f"SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'size_mb' "
                f"FROM information_schema.tables WHERE table_schema = '{self.db_name}'"
            ).fetchone()

            size_mb = float(result[0]) if result and result[0] else 0.0

            # Try to get total available space (may not be available in all OceanBase versions)
            try:
                result = self.client.perform_raw_text_sql(
                    "SELECT ROUND(SUM(total_size) / 1024 / 1024 / 1024, 2) AS 'total_gb' "
                    "FROM oceanbase.__all_disk_stat"
                ).fetchone()
                total_gb = float(result[0]) if result and result[0] else None
            except Exception:
                # Fallback: estimate total space (100GB default if not available)
                total_gb = 100.0

            return {
                "storage_used": f"{size_mb:.2f}MB",
                "storage_total": f"{total_gb:.2f}GB" if total_gb else "N/A"
            }
        except Exception as e:
            logger.warning(f"Failed to get storage info: {str(e)}")
            return {
                "storage_used": "N/A",
                "storage_total": "N/A"
            }