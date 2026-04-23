def execute(self) -> tuple[int, list]:
        """Execute migration"""
        current_ts = self.current_timestamp()
        rows_inserted = 0

        # Check if tenant_model_provider exists (dependency)
        if not self.db.table_exists("tenant_model_provider"):
            logger.error("Dependency table 'tenant_model_provider' does not exist. "
                        "Please run 'tenant_model_provider' stage first.")
            return 0, []

        # Check if target table exists
        if not self.db.table_exists("tenant_model_instance"):
            if self.dry_run:
                logger.info("[DRY RUN] Target table 'tenant_model_instance' does not exist. "
                           "Use --execute to create and populate the table.")
                return 0, []
            logger.info("Target table 'tenant_model_instance' does not exist, will create")
            self.create_target_table()

        # If create_table_only mode, skip data migration
        if self.create_table_only:
            logger.info("[CREATE TABLE ONLY] Target table created/verified, skipping data migration")
            return 0, self.target_tables

        # Get records from tenant_llm with provider_id lookup
        # Group by tenant_id, llm_factory, api_key to get distinct records
        # instance_name = llm_factory, provider_id from tenant_model_provider, api_key from tenant_llm
        cursor = self.db.execute_sql(
            "SELECT tl.tenant_id, tl.llm_factory, tl.api_key, MAX(tl.status) as status, tmp.id as provider_id "
            "FROM tenant_llm tl "
            "INNER JOIN tenant_model_provider tmp ON tmp.tenant_id = tl.tenant_id AND tmp.provider_name = tl.llm_factory "
            "WHERE NOT EXISTS ("
            "  SELECT 1 FROM tenant_model_instance tmi "
            "  WHERE tmi.provider_id = tmp.id AND tmi.api_key = tl.api_key"
            ") "
            "GROUP BY tl.tenant_id, tl.llm_factory, tl.api_key, tmp.id"
        )

        records = cursor.fetchall()

        if not records:
            logger.info("No records to migrate")
            return 0, []

        logger.info(f"Migrating {len(records)} tenant_model_instance records...")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would insert {len(records)} records")
            for tenant_id, llm_factory, api_key, status, provider_id in records[:5]:
                logger.info(f"  instance_name={llm_factory}, provider_id={provider_id}, api_key=***")
            if len(records) > 5:
                logger.info(f"  ... and {len(records) - 5} more records")
            return len(records), self.target_tables

        # Insert records in batches
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            values = []
            for tenant_id, llm_factory, api_key, status, provider_id in batch:
                record_id = self.generate_uuid()
                instance_name = llm_factory.replace("'", "''") if llm_factory else ""
                api_key_escaped = api_key.replace("'", "''") if api_key else ""
                status_val = status if status else "active"
                values.append(f"('{record_id}', '{instance_name}', '{provider_id}', "
                            f"'{api_key_escaped}', '{status_val}', "
                            f"{current_ts}, FROM_UNIXTIME({current_ts}), "
                            f"{current_ts}, FROM_UNIXTIME({current_ts}))")

            insert_sql = f"""
                INSERT INTO tenant_model_instance 
                (id, instance_name, provider_id, api_key, status, create_time, create_date, update_time, update_date)
                VALUES {', '.join(values)}
            """
            self.db.execute_sql(insert_sql)
            rows_inserted += len(batch)
            logger.info(f"Inserted batch {i // batch_size + 1}: {len(batch)} records")

        return rows_inserted, self.target_tables