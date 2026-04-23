def _update_metadata(
        self,
        session: Session,
        statistic_id: str,
        new_metadata: StatisticMetaData,
        old_metadata_dict: dict[str, tuple[int, StatisticMetaData]],
    ) -> tuple[str | None, int]:
        """Update metadata in the database.

        This call is not thread-safe and must be called from the
        recorder thread.
        """
        if "mean_type" not in new_metadata:
            # To maintain backward compatibility after adding 'mean_type' in schema version 49,
            # we must still check for its presence. Even though type hints suggest it should always exist,
            # custom integrations might omit it, so we need to guard against that.
            new_metadata["mean_type"] = (  # type: ignore[unreachable]
                StatisticMeanType.ARITHMETIC
                if new_metadata["has_mean"]
                else StatisticMeanType.NONE
            )
        metadata_id, old_metadata = old_metadata_dict[statistic_id]
        if not (
            old_metadata["mean_type"] != new_metadata["mean_type"]
            or old_metadata["has_sum"] != new_metadata["has_sum"]
            or old_metadata["name"] != new_metadata["name"]
            or old_metadata["unit_class"] != new_metadata["unit_class"]
            or old_metadata["unit_of_measurement"]
            != new_metadata["unit_of_measurement"]
        ):
            return None, metadata_id

        self._assert_in_recorder_thread()
        session.query(StatisticsMeta).filter_by(statistic_id=statistic_id).update(
            {
                StatisticsMeta.mean_type: new_metadata["mean_type"],
                StatisticsMeta.has_sum: new_metadata["has_sum"],
                StatisticsMeta.name: new_metadata["name"],
                StatisticsMeta.unit_class: new_metadata["unit_class"],
                StatisticsMeta.unit_of_measurement: new_metadata["unit_of_measurement"],
            },
            synchronize_session=False,
        )
        self._clear_cache([statistic_id])
        _LOGGER.debug(
            "Updated statistics metadata for %s, old_metadata: %s, new_metadata: %s",
            statistic_id,
            old_metadata,
            new_metadata,
        )
        return statistic_id, metadata_id