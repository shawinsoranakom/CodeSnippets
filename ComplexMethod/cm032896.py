def adjust_chunk_pagerank_fea(
        self,
        chunk_id: str,
        index_name: str,
        knowledgebase_id: str,
        delta: int,
        min_weight: int,
        max_weight: int,
        row_id: int | None = None,
        max_retries: int = 2,
    ) -> bool:
        """Adjust pagerank_fea on one chunk row in Infinity.

        Uses row_id for a targeted update when available. If the row_id is
        stale (concurrent update changed it), re-reads the current row_id and
        retries up to *max_retries* times.
        """
        table_name = f"{index_name}_{knowledgebase_id}"
        for attempt in range(max_retries + 1):
            inf_conn = self.connPool.get_conn()
            try:
                db_instance = inf_conn.get_database(self.dbName)
                table_instance = db_instance.get_table(table_name)

                if row_id is None:
                    df, _ = table_instance.output(
                        [PAGERANK_FLD, "row_id()"]
                    ).filter(f"id = '{chunk_id}'").to_df()
                    if df.empty:
                        self.logger.warning(
                            "adjust_chunk_pagerank_fea: chunk %s not found in %s",
                            chunk_id, table_name,
                        )
                        return False
                    current_weight = int(float(df[PAGERANK_FLD].iloc[0] or 0))
                    row_id = int(df["row_id"].iloc[0])
                else:
                    df, _ = table_instance.output(
                        [PAGERANK_FLD]
                    ).filter(f"id = '{chunk_id}'").to_df()
                    if df.empty:
                        return False
                    current_weight = int(float(df[PAGERANK_FLD].iloc[0] or 0))

                new_weight = max(min_weight, min(max_weight, current_weight + delta))

                table_instance.update(
                    f"_row_id = {row_id}",
                    {PAGERANK_FLD: new_weight},
                )
                self.logger.info(
                    "adjust_chunk_pagerank_fea(chunk=%s, table=%s): %s -> %s via row_id=%s",
                    chunk_id, table_name, current_weight, new_weight, row_id,
                )
                return True

            except InfinityException as e:
                if attempt < max_retries:
                    self.logger.warning(
                        "adjust_chunk_pagerank_fea stale row_id=%s for chunk %s (attempt %s/%s): %s",
                        row_id, chunk_id, attempt + 1, max_retries, e,
                    )
                    row_id = None
                    continue
                self.logger.error(
                    "adjust_chunk_pagerank_fea failed for chunk %s after %s attempts: %s",
                    chunk_id, max_retries + 1, e,
                )
                return False
            except Exception as e:
                self.logger.error(
                    "adjust_chunk_pagerank_fea error for chunk %s: %s", chunk_id, e,
                )
                return False
            finally:
                self.connPool.release_conn(inf_conn)
        return False