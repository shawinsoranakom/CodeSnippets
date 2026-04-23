def local_step():
        nonlocal use_collectives
        nonlocal metadata

        # Use global metadata if available, otherwise fallback to rank local metadata
        global_metadata_exc: Exception | None = None
        rank_metadata_exc: Exception | None = None
        try:
            metadata = storage_reader.read_metadata()
        except Exception as e:
            global_metadata_exc = e
            logger.warning(
                "Global metadata is not found. Falling back to rank local metadata.",
                exc_info=True,
            )

        if (
            not metadata
            and "kwargs" in inspect.signature(storage_reader.read_metadata).parameters
        ):
            try:
                metadata = storage_reader.read_metadata(rank=distW.rank)
                use_collectives = False
            except Exception as e:
                rank_metadata_exc = e
                logger.warning("Rank local metadata is not found.", exc_info=True)

        if planner is None:
            raise AssertionError("planner is None")
        if metadata is None:
            error_parts = ["metadata is None"]
            if global_metadata_exc is not None:
                error_parts.append(
                    f"global metadata read failed: {global_metadata_exc}"
                )
            if rank_metadata_exc is not None:
                error_parts.append(
                    f"rank local metadata read failed: {rank_metadata_exc}"
                )
            raise AssertionError("; ".join(error_parts))
        planner.set_up_planner(state_dict, metadata, distW.is_coordinator)

        if (
            "kwargs"
            in inspect.signature(storage_reader.set_up_storage_reader).parameters
        ):
            storage_reader.set_up_storage_reader(
                metadata,
                distW.is_coordinator,
                rank=distW.rank,
                use_collectives=use_collectives,
            )
        else:
            storage_reader.set_up_storage_reader(metadata, distW.is_coordinator)

        local_plan = planner.create_local_plan()
        local_plan = storage_reader.prepare_local_plan(local_plan)
        return local_plan