def execute(self) -> tuple[int, list]:
        """Execute migration"""
        current_ts = self.current_timestamp()
        rows_inserted = 0

        # Check if target table exists
        if not self.db.table_exists("tenant_model_provider"):
            if self.dry_run:
                logger.info("[DRY RUN] Target table 'tenant_model_provider' does not exist. "
                           "Use --execute to create and populate the table.")
                return 0, []
            logger.info("Target table 'tenant_model_provider' does not exist, will create")
            self.create_target_table()

        # If create_table_only mode, skip data migration
        if self.create_table_only:
            logger.info("[CREATE TABLE ONLY] Target table created/verified, skipping data migration")
            return 0, self.target_tables

        # Get distinct tenant_id, llm_factory pairs that don't exist in target
        cursor = self.db.execute_sql(
            "SELECT DISTINCT tenant_id, llm_factory FROM tenant_llm t1 "
            "WHERE NOT EXISTS ("
            "  SELECT 1 FROM tenant_model_provider t2 "
            "  WHERE t2.tenant_id = t1.tenant_id AND t2.provider_name = t1.llm_factory"
            ")"
        )

        records = cursor.fetchall()

        if not records:
            logger.info("No records to migrate")
            return 0, []

        logger.info(f"Migrating {len(records)} unique tenant_id/llm_factory pairs...")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would insert {len(records)} records")
            return len(records), self.target_tables

        # Insert records in batches
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            values = []
            for tenant_id, llm_factory in batch:
                record_id = self.generate_uuid()
                values.append(f"('{record_id}', '{llm_factory}', '{tenant_id}', "
                            f"{current_ts}, FROM_UNIXTIME({current_ts}), "
                            f"{current_ts}, FROM_UNIXTIME({current_ts}))")

            insert_sql = f"""
                INSERT INTO tenant_model_provider 
                (id, provider_name, tenant_id, create_time, create_date, update_time, update_date)
                VALUES {', '.join(values)}
            """
            self.db.execute_sql(insert_sql)
            rows_inserted += len(batch)
            logger.info(f"Inserted batch {i // batch_size + 1}: {len(batch)} records")

        return rows_inserted, self.target_tables