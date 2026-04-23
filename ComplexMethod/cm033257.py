def _drop_empty_metadata_table(cls, index_name: str, tenant_id: str) -> None:
        """
        Check if metadata table is empty and drop it if so.
        Uses optimized count query instead of full search.
        This prevents accumulation of empty metadata tables.

        Args:
            index_name: Metadata table/index name
            tenant_id: Tenant ID
        """
        try:
            logging.debug(f"[DROP EMPTY TABLE] Starting empty table check for: {index_name}")

            # Check if table exists first (cheap operation)
            if not settings.docStoreConn.index_exist(index_name, ""):
                logging.debug(f"[DROP EMPTY TABLE] Metadata table {index_name} does not exist, skipping")
                return

            logging.debug(f"[DROP EMPTY TABLE] Table {index_name} exists, checking if empty...")

            # Use ES count API for accurate count
            # Note: No need to refresh since delete operation already uses refresh=True
            try:
                count_response = settings.docStoreConn.es.count(index=index_name)
                total_count = count_response['count']
                logging.debug(f"[DROP EMPTY TABLE] ES count API result: {total_count} documents")
                is_empty = (total_count == 0)
            except Exception as e:
                logging.warning(f"[DROP EMPTY TABLE] Count API failed, falling back to search: {e}")
                # Fallback to search if count fails
                results = settings.docStoreConn.search(
                    select_fields=["id"],
                    highlight_fields=[],
                    condition={},
                    match_expressions=[],
                    order_by=OrderByExpr(),
                    offset=0,
                    limit=1,  # Only need 1 result to know if table is non-empty
                    index_names=index_name,
                    knowledgebase_ids=[""]  # Metadata tables don't filter by KB
                )

                logging.debug(f"[DROP EMPTY TABLE] Search results type: {type(results)}, results: {results}")

                # Check if empty based on return type (fallback search only)
                if isinstance(results, tuple) and len(results) == 2:
                    # Infinity returns (DataFrame, int)
                    df, total = results
                    logging.debug(f"[DROP EMPTY TABLE] Infinity format - total: {total}, df length: {len(df) if hasattr(df, '__len__') else 'N/A'}")
                    is_empty = (total == 0 or (hasattr(df, '__len__') and len(df) == 0))
                elif hasattr(results, 'get') and 'hits' in results:
                    # ES format - MUST check this before hasattr(results, '__len__')
                    # because ES response objects also have __len__
                    total = results.get('hits', {}).get('total', {})
                    hits = results.get('hits', {}).get('hits', [])

                    # ES 7.x+: total is a dict like {'value': 0, 'relation': 'eq'}
                    # ES 6.x: total is an int
                    if isinstance(total, dict):
                        total_count = total.get('value', 0)
                    else:
                        total_count = total

                    logging.debug(f"[DROP EMPTY TABLE] ES format - total: {total_count}, hits count: {len(hits)}")
                    is_empty = (total_count == 0 or len(hits) == 0)
                elif hasattr(results, '__len__'):
                    # DataFrame or list (check this AFTER ES format)
                    result_len = len(results)
                    logging.debug(f"[DROP EMPTY TABLE] List/DataFrame format - length: {result_len}")
                    is_empty = result_len == 0
                else:
                    logging.warning(f"[DROP EMPTY TABLE] Unknown result format: {type(results)}")
                    is_empty = False

            if is_empty:
                logging.debug(f"[DROP EMPTY TABLE] Metadata table {index_name} is empty, dropping it")
                drop_result = settings.docStoreConn.delete_idx(index_name, "")
                logging.debug(f"[DROP EMPTY TABLE] Drop result: {drop_result}")
            else:
                logging.debug(f"[DROP EMPTY TABLE] Metadata table {index_name} still has documents, keeping it")

        except Exception as e:
            # Log but don't fail - metadata deletion was successful
            logging.error(f"[DROP EMPTY TABLE] Failed to check/drop empty metadata table {index_name}: {e}")