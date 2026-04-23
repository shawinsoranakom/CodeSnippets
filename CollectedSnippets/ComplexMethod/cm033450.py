def migrate(
        self,
        es_index: str,
        ob_table: str,
        batch_size: int = 1000,
        resume: bool = False,
        verify_after: bool = True,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """
        Execute full migration from ES to OceanBase for RAGFlow data.

        Args:
            es_index: Source Elasticsearch index
            ob_table: Target OceanBase table
            batch_size: Documents per batch
            resume: Resume from previous progress
            verify_after: Run verification after migration
            on_progress: Progress callback (migrated, total)

        Returns:
            Migration result dictionary
        """
        start_time = time.time()
        result = {
            "success": False,
            "es_index": es_index,
            "ob_table": ob_table,
            "total_documents": 0,
            "migrated_documents": 0,
            "failed_documents": 0,
            "duration_seconds": 0,
            "verification": None,
            "error": None,
        }

        progress: MigrationProgress | None = None

        try:
            # Step 1: Check connections
            console.print("[bold blue]Step 1: Checking connections...[/]")
            self._check_connections()

            # Step 2: Analyze ES index
            console.print("\n[bold blue]Step 2: Analyzing ES index...[/]")
            analysis = self._analyze_es_index(es_index)

            # Auto-detect vector size from ES mapping
            vector_size = 768  # Default fallback
            if analysis["vector_fields"]:
                vector_size = analysis["vector_fields"][0]["dimension"]
                console.print(f"  [green]Auto-detected vector dimension: {vector_size}[/]")
            else:
                console.print(f"  [yellow]No vector fields found, using default: {vector_size}[/]")
            console.print(f"  Known RAGFlow fields: {len(analysis['known_fields'])}")
            if analysis["unknown_fields"]:
                console.print(f"  [yellow]Unknown fields (will be stored in 'extra'): {analysis['unknown_fields']}[/]")

            # Step 3: Get total document count
            total_docs = self.es_client.count_documents(es_index)
            console.print(f"  Total documents: {total_docs:,}")

            result["total_documents"] = total_docs

            if total_docs == 0:
                console.print("[yellow]No documents to migrate[/]")
                result["success"] = True
                return result

            # Step 4: Handle resume or fresh start
            if resume and self.progress_manager.can_resume(es_index, ob_table):
                console.print("\n[bold yellow]Resuming from previous progress...[/]")
                progress = self.progress_manager.load_progress(es_index, ob_table)
                console.print(
                    f"  Previously migrated: {progress.migrated_documents:,} documents"
                )
            else:
                # Fresh start - check if table already exists
                if self.ob_client.table_exists(ob_table):
                    raise RuntimeError(
                        f"Table '{ob_table}' already exists in OceanBase. "
                        f"Migration aborted to prevent data conflicts. "
                        f"Please drop the table manually or use a different table name."
                    )

                progress = self.progress_manager.create_progress(
                    es_index, ob_table, total_docs
                )

            # Step 5: Create table if needed
            if not progress.table_created:
                console.print("\n[bold blue]Step 3: Creating OceanBase table...[/]")
                if not self.ob_client.table_exists(ob_table):
                    self.ob_client.create_ragflow_table(
                        table_name=ob_table,
                        vector_size=vector_size,
                        create_indexes=True,
                        create_fts_indexes=True,
                    )
                    console.print(f"  Created table '{ob_table}' with RAGFlow schema")
                else:
                    console.print(f"  Table '{ob_table}' already exists")
                    # Check and add vector column if needed
                    self.ob_client.add_vector_column(ob_table, vector_size)

                progress.table_created = True
                progress.indexes_created = True
                progress.schema_converted = True
                self.progress_manager.save_progress(progress)

            # Step 6: Migrate data
            console.print("\n[bold blue]Step 4: Migrating data...[/]")
            data_converter = RAGFlowDataConverter()

            migrated = self._migrate_data(
                es_index=es_index,
                ob_table=ob_table,
                data_converter=data_converter,
                progress=progress,
                batch_size=batch_size,
                on_progress=on_progress,
            )

            result["migrated_documents"] = migrated
            result["failed_documents"] = progress.failed_documents

            # Step 7: Mark completed
            self.progress_manager.mark_completed(progress)

            # Step 8: Verify (optional)
            if verify_after:
                console.print("\n[bold blue]Step 5: Verifying migration...[/]")
                verifier = MigrationVerifier(self.es_client, self.ob_client)
                verification = verifier.verify(
                    es_index, ob_table, 
                    primary_key="id"
                )
                result["verification"] = {
                    "passed": verification.passed,
                    "message": verification.message,
                    "es_count": verification.es_count,
                    "ob_count": verification.ob_count,
                    "sample_match_rate": verification.sample_match_rate,
                }
                console.print(verifier.generate_report(verification))

            result["success"] = True
            result["duration_seconds"] = time.time() - start_time

            console.print(
                f"\n[bold green]Migration completed successfully![/]"
                f"\n  Total: {result['total_documents']:,} documents"
                f"\n  Migrated: {result['migrated_documents']:,} documents"
                f"\n  Failed: {result['failed_documents']:,} documents"
                f"\n  Duration: {result['duration_seconds']:.1f} seconds"
            )

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Migration interrupted by user[/]")
            if progress:
                self.progress_manager.mark_paused(progress)
            result["error"] = "Interrupted by user"

        except Exception as e:
            logger.exception("Migration failed")
            if progress:
                self.progress_manager.mark_failed(progress, str(e))
            result["error"] = str(e)
            console.print(f"\n[bold red]Migration failed: {e}[/]")

        return result