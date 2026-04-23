def execute(self) -> tuple[int, list]:
        """Execute migration"""
        current_ts = self.current_timestamp()
        rows_inserted = 0

        # Check if tenant_model_provider exists (dependency)
        if not self.db.table_exists("tenant_model_provider"):
            logger.error("Dependency table 'tenant_model_provider' does not exist. "
                        "Please run 'tenant_model_provider' stage first.")
            return 0, []

        # Check if tenant_model_instance exists (dependency)
        if not self.db.table_exists("tenant_model_instance"):
            logger.error("Dependency table 'tenant_model_instance' does not exist. "
                        "Please run 'tenant_model_instance' stage first.")
            return 0, []

        # Check if target table exists
        if not self.db.table_exists("tenant_model"):
            if self.dry_run:
                logger.info("[DRY RUN] Target table 'tenant_model' does not exist. "
                           "Use --execute to create and populate the table.")
                return 0, []
            logger.info("Target table 'tenant_model' does not exist, will create")
            self.create_target_table()

        # If create_table_only mode, skip data migration
        if self.create_table_only:
            logger.info("[CREATE TABLE ONLY] Target table created/verified, skipping data migration")
            return 0, self.target_tables

        # Get records from tenant_llm with provider_id and instance_id lookup
        # Only migrate records where status='0'
        cursor = self.db.execute_sql(
            "SELECT tl.id, tl.llm_name, tmp.id as provider_id, tmi.id as instance_id, "
            "       tl.model_type, tl.status "
            "FROM tenant_llm tl "
            "INNER JOIN tenant_model_provider tmp ON tmp.tenant_id = tl.tenant_id AND tmp.provider_name = tl.llm_factory "
            "INNER JOIN tenant_model_instance tmi ON tmi.provider_id = tmp.id AND tmi.api_key = tl.api_key "
            "WHERE tl.status = '0' "
            "AND NOT EXISTS ("
            "  SELECT 1 FROM tenant_model tm "
            "  WHERE tm.provider_id = tmp.id AND tm.model_name = tl.llm_name AND tm.instance_id = tmi.id"
            ")"
        )

        records = cursor.fetchall()

        if not records:
            logger.info("No records to migrate")
            return 0, []

        logger.info(f"Migrating {len(records)} tenant_model records...")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would insert {len(records)} records")
            for source_id, llm_name, provider_id, instance_id, model_type, status in records[:5]:
                logger.info(f"  model_name={llm_name}, provider_id={provider_id}, "
                           f"instance_id={instance_id}, model_type={model_type}")
            if len(records) > 5:
                logger.info(f"  ... and {len(records) - 5} more records")
            return len(records), self.target_tables

        # Insert records in batches
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            values = []
            for source_id, llm_name, provider_id, instance_id, model_type, status in batch:
                record_id = self.generate_uuid()
                model_name_escaped = llm_name.replace("'", "''") if llm_name else ""
                model_type_escaped = model_type.replace("'", "''") if model_type else ""
                status_val = status if status else "active"
                values.append(f"('{record_id}', '{model_name_escaped}', '{provider_id}', "
                            f"'{instance_id}', '{model_type_escaped}', '{status_val}', "
                            f"{current_ts}, FROM_UNIXTIME({current_ts}), "
                            f"{current_ts}, FROM_UNIXTIME({current_ts}))")

            insert_sql = f"""
                INSERT INTO tenant_model 
                (id, model_name, provider_id, instance_id, model_type, status, 
                 create_time, create_date, update_time, update_date)
                VALUES {', '.join(values)}
            """
            self.db.execute_sql(insert_sql)
            rows_inserted += len(batch)
            logger.info(f"Inserted batch {i // batch_size + 1}: {len(batch)} records")

        return rows_inserted, self.target_tables