async def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:

        exa = Exa(credentials.api_key.get_secret_value())

        entity = None
        if input_data.search_entity_type == SearchEntityType.COMPANY:
            entity = WebsetCompanyEntity(type="company")
        elif input_data.search_entity_type == SearchEntityType.PERSON:
            entity = WebsetPersonEntity(type="person")
        elif input_data.search_entity_type == SearchEntityType.ARTICLE:
            entity = WebsetArticleEntity(type="article")
        elif input_data.search_entity_type == SearchEntityType.RESEARCH_PAPER:
            entity = WebsetResearchPaperEntity(type="research_paper")
        elif (
            input_data.search_entity_type == SearchEntityType.CUSTOM
            and input_data.search_entity_description
        ):
            entity = WebsetCustomEntity(
                type="custom", description=input_data.search_entity_description
            )

        criteria = None
        if input_data.search_criteria:
            criteria = [
                CreateCriterionParameters(description=item)
                for item in input_data.search_criteria
            ]

        exclude_items = None
        if input_data.search_exclude_sources:
            exclude_items = []
            for idx, src_id in enumerate(input_data.search_exclude_sources):
                src_type = None
                if input_data.search_exclude_types and idx < len(
                    input_data.search_exclude_types
                ):
                    src_type = input_data.search_exclude_types[idx]
                # Default to IMPORT if type missing
                if src_type == SearchType.WEBSET:
                    source_enum = ImportSource.webset
                else:
                    source_enum = ImportSource.import_
                exclude_items.append(ExcludeItem(source=source_enum, id=src_id))

        scope_items = None
        if input_data.search_scope_sources:
            scope_items = []
            for idx, src_id in enumerate(input_data.search_scope_sources):
                src_type = None
                if input_data.search_scope_types and idx < len(
                    input_data.search_scope_types
                ):
                    src_type = input_data.search_scope_types[idx]
                relationship = None
                if input_data.search_scope_relationships and idx < len(
                    input_data.search_scope_relationships
                ):
                    rel_def = input_data.search_scope_relationships[idx]
                    lim = None
                    if input_data.search_scope_relationship_limits and idx < len(
                        input_data.search_scope_relationship_limits
                    ):
                        lim = input_data.search_scope_relationship_limits[idx]
                    relationship = ScopeRelationship(definition=rel_def, limit=lim)
                if src_type == SearchType.WEBSET:
                    src_enum = ScopeSourceType.webset
                else:
                    src_enum = ScopeSourceType.import_
                scope_items.append(
                    ScopeItem(source=src_enum, id=src_id, relationship=relationship)
                )

        search_params = None
        if input_data.search_query:
            search_params = CreateWebsetParametersSearch(
                query=input_data.search_query,
                count=input_data.search_count,
                entity=entity,
                criteria=criteria,
                exclude=exclude_items,
                scope=scope_items,
            )

        imports_params = None
        if input_data.import_sources:
            imports_params = []
            for idx, src_id in enumerate(input_data.import_sources):
                src_type = None
                if input_data.import_types and idx < len(input_data.import_types):
                    src_type = input_data.import_types[idx]
                if src_type == SearchType.WEBSET:
                    source_enum = ImportSource.webset
                else:
                    source_enum = ImportSource.import_
                imports_params.append(ImportItem(source=source_enum, id=src_id))

        enrichments_params = None
        if input_data.enrichment_descriptions:
            enrichments_params = []
            for idx, desc in enumerate(input_data.enrichment_descriptions):
                fmt = None
                if input_data.enrichment_formats and idx < len(
                    input_data.enrichment_formats
                ):
                    fmt_enum = input_data.enrichment_formats[idx]
                    if fmt_enum is not None:
                        fmt = Format(
                            fmt_enum.value if isinstance(fmt_enum, Enum) else fmt_enum
                        )
                options_list = None
                if input_data.enrichment_options and idx < len(
                    input_data.enrichment_options
                ):
                    raw_opts = input_data.enrichment_options[idx]
                    if raw_opts:
                        options_list = [Option(label=o) for o in raw_opts]
                metadata_obj = None
                if input_data.enrichment_metadata and idx < len(
                    input_data.enrichment_metadata
                ):
                    metadata_obj = input_data.enrichment_metadata[idx]
                enrichments_params.append(
                    CreateEnrichmentParameters(
                        description=desc,
                        format=fmt,
                        options=options_list,
                        metadata=metadata_obj,
                    )
                )

        try:
            start_time = time.time()
            webset = exa.websets.create(
                params=CreateWebsetParameters(
                    search=search_params,
                    imports=imports_params,
                    enrichments=enrichments_params,
                    external_id=input_data.external_id,
                    metadata=input_data.metadata,
                )
            )

            webset_result = Webset.model_validate(webset.model_dump(by_alias=True))

            # If wait_for_initial_results is True, poll for completion
            if input_data.wait_for_initial_results and search_params:
                final_webset = exa.websets.wait_until_idle(
                    id=webset_result.id,
                    timeout=input_data.polling_timeout,
                    poll_interval=5,
                )
                completion_time = time.time() - start_time

                item_count = 0
                if final_webset.searches:
                    for search in final_webset.searches:
                        if search.progress:
                            item_count += search.progress.found

                yield "webset", webset_result
                yield "initial_item_count", item_count
                yield "completion_time", completion_time
            else:
                yield "webset", webset_result

        except ValueError as e:
            raise ValueError(f"Invalid webset configuration: {e}") from e