async def get_jobs(request):
            """List all jobs with filtering, sorting, and pagination.

            Query parameters:
                status: Filter by status (comma-separated): pending, in_progress, completed, failed
                workflow_id: Filter by workflow ID
                sort_by: Sort field: created_at (default), execution_duration
                sort_order: Sort direction: asc, desc (default)
                limit: Max items to return (positive integer)
                offset: Items to skip (non-negative integer, default 0)
            """
            query = request.rel_url.query

            status_param = query.get('status')
            workflow_id = query.get('workflow_id')
            sort_by = query.get('sort_by', 'created_at').lower()
            sort_order = query.get('sort_order', 'desc').lower()

            status_filter = None
            if status_param:
                status_filter = [s.strip().lower() for s in status_param.split(',') if s.strip()]
                invalid_statuses = [s for s in status_filter if s not in JobStatus.ALL]
                if invalid_statuses:
                    return web.json_response(
                        {"error": f"Invalid status value(s): {', '.join(invalid_statuses)}. Valid values: {', '.join(JobStatus.ALL)}"},
                        status=400
                    )

            if sort_by not in {'created_at', 'execution_duration'}:
                return web.json_response(
                    {"error": "sort_by must be 'created_at' or 'execution_duration'"},
                    status=400
                )

            if sort_order not in {'asc', 'desc'}:
                return web.json_response(
                    {"error": "sort_order must be 'asc' or 'desc'"},
                    status=400
                )

            limit = None

            # If limit is provided, validate that it is a positive integer, else continue without a limit
            if 'limit' in query:
                try:
                    limit = int(query.get('limit'))
                    if limit <= 0:
                        return web.json_response(
                            {"error": "limit must be a positive integer"},
                            status=400
                        )
                except (ValueError, TypeError):
                    return web.json_response(
                        {"error": "limit must be an integer"},
                        status=400
                    )

            offset = 0
            if 'offset' in query:
                try:
                    offset = int(query.get('offset'))
                    if offset < 0:
                        offset = 0
                except (ValueError, TypeError):
                    return web.json_response(
                        {"error": "offset must be an integer"},
                        status=400
                    )

            running, queued = self.prompt_queue.get_current_queue_volatile()
            history = self.prompt_queue.get_history()

            running = _remove_sensitive_from_queue(running)
            queued = _remove_sensitive_from_queue(queued)

            jobs, total = get_all_jobs(
                running, queued, history,
                status_filter=status_filter,
                workflow_id=workflow_id,
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                offset=offset
            )

            has_more = (offset + len(jobs)) < total

            return web.json_response({
                'jobs': jobs,
                'pagination': {
                    'offset': offset,
                    'limit': limit,
                    'total': total,
                    'has_more': has_more
                }
            })