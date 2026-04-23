async def get_sources(
        self, page: int = 1, per_page: int = 10, category: Optional[str] = None, search: Optional[str] = None, include_inactive: bool = False
    ) -> PaginatedSources:
        """Get sources with pagination and filtering."""
        try:
            query_parts = ["SELECT s.id, s.name, s.url, s.description, s.is_active, s.created_at", "FROM sources s", "WHERE 1=1"]
            query_params = []
            if not include_inactive:
                query_parts.append("AND s.is_active = 1")
            if category:
                query_parts.append("""
                    AND EXISTS (
                        SELECT 1 FROM source_categories sc 
                        JOIN categories c ON sc.category_id = c.id
                        WHERE sc.source_id = s.id AND c.name = ?
                    )
                """)
                query_params.append(category)
            if search:
                query_parts.append("AND (s.name LIKE ? OR s.description LIKE ?)")
                search_param = f"%{search}%"
                query_params.extend([search_param, search_param])
            count_query = " ".join(query_parts).replace("SELECT s.id, s.name, s.url, s.description, s.is_active, s.created_at", "SELECT COUNT(*)")
            total_sources = await sources_db.execute_query(count_query, tuple(query_params), fetch=True, fetch_one=True)
            total_count = total_sources.get("COUNT(*)", 0) if total_sources else 0
            query_parts.append("ORDER BY s.name")
            offset = (page - 1) * per_page
            query_parts.append("LIMIT ? OFFSET ?")
            query_params.extend([per_page, offset])
            final_query = " ".join(query_parts)
            sources = await sources_db.execute_query(final_query, tuple(query_params), fetch=True)
            for source in sources:
                source["categories"] = await self.get_source_categories(source["id"])
                source["last_crawled"] = await self.get_source_last_crawled(source["id"])
                source["website"] = source["url"]
                if source["categories"] and isinstance(source["categories"], list):
                    source["category"] = source["categories"][0] if source["categories"] else ""
            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
            has_next = page < total_pages
            has_prev = page > 1
            return PaginatedSources(
                items=sources, total=total_count, page=page, per_page=per_page, total_pages=total_pages, has_next=has_next, has_prev=has_prev
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching sources: {str(e)}")