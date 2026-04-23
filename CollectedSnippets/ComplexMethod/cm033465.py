def check(self) -> bool:
        """Check if migration is needed"""
        # Check if source table exists
        if not self.db.table_exists("tenant_llm"):
            logger.warning("Source table 'tenant_llm' does not exist")
            return False

        # Check if tenant_model_provider exists (dependency)
        if not self.db.table_exists("tenant_model_provider"):
            if self.dry_run:
                logger.info("[DRY RUN] Dependency table 'tenant_model_provider' does not exist. "
                           "Run 'tenant_model_provider' stage first or use --execute.")
                return False
            logger.warning("Dependency table 'tenant_model_provider' does not exist. "
                          "Please run 'tenant_model_provider' stage first.")
            return False

        # Check if tenant_model_instance exists (dependency)
        if not self.db.table_exists("tenant_model_instance"):
            if self.dry_run:
                logger.info("[DRY RUN] Dependency table 'tenant_model_instance' does not exist. "
                           "Run 'tenant_model_instance' stage first or use --execute.")
                return False
            logger.warning("Dependency table 'tenant_model_instance' does not exist. "
                          "Please run 'tenant_model_instance' stage first.")
            return False

        # Check if target table exists
        if not self.db.table_exists("tenant_model"):
            if self.dry_run:
                logger.info("[DRY RUN] Target table 'tenant_model' does not exist. "
                           "Use --execute to create and populate the table.")
                return False
            logger.info("Target table 'tenant_model' does not exist, will create")
            return True

        # Check if there's data to migrate (only status='0' records)
        cursor = self.db.execute_sql(
            "SELECT COUNT(*) FROM ("
            "  SELECT tl.id "
            "  FROM tenant_llm tl "
            "  INNER JOIN tenant_model_provider tmp ON tmp.tenant_id = tl.tenant_id AND tmp.provider_name = tl.llm_factory "
            "  INNER JOIN tenant_model_instance tmi ON tmi.provider_id = tmp.id AND tmi.api_key = tl.api_key "
            "  WHERE tl.status = '0' "
            "  AND NOT EXISTS ("
            "    SELECT 1 FROM tenant_model tm "
            "    WHERE tm.provider_id = tmp.id AND tm.model_name = tl.llm_name AND tm.instance_id = tmi.id"
            "  )"
            ") AS distinct_records"
        )
        count = cursor.fetchone()[0]

        if count == 0:
            logger.info("No new data to migrate from tenant_llm to tenant_model (status='0' only)")
            return False

        logger.info(f"Found {count} rows to migrate from tenant_llm to tenant_model")
        return True