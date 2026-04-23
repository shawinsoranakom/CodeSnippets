def _maybe_apply_prompt_updates(
        self,
        mm_items: MultiModalDataItems,
        prompt_ids: list[int],
        mm_kwargs: MultiModalKwargsItems,
        mm_prompt_updates: MultiModalPromptUpdates,
        is_update_applied: bool,
    ) -> tuple[list[int], str, Mapping[str, list[PlaceholderFeaturesInfo]]]:
        """
        Qwen3-Omni reimplements this function to handle `use_audio_in_video`.
        """
        mm_item_counts = mm_items.get_all_counts()
        self._validate_mm_kwargs(mm_kwargs, mm_item_counts)

        use_audio_in_video = False
        if "video" in mm_kwargs:
            for item in mm_kwargs["video"]:
                if item and item["use_audio_in_video"].data:
                    use_audio_in_video = True
                else:
                    use_audio_in_video = False
            # for mutilmodality cache
            if any(item is None for item in mm_kwargs["video"]):
                video_token_id = self.info.get_hf_config().video_token_id
                audio_token_id = self.info.get_hf_config().audio_token_id
                video_audio_item_num = sum(
                    id in (video_token_id, audio_token_id) for id in prompt_ids
                )
                audio_updates_num = len(mm_prompt_updates.get("audio", []))
                video_updates_num = len(mm_prompt_updates.get("video", []))
                if video_audio_item_num != video_updates_num + audio_updates_num:
                    use_audio_in_video = True

        # normal case with `use_audio_in_video=False`
        if is_update_applied:
            mm_placeholders = self._find_mm_placeholders(
                prompt_ids,
                mm_prompt_updates,
            )
            self._validate_mm_placeholders(
                mm_placeholders,
                mm_item_counts,
            )
        else:
            if use_audio_in_video and "audio" in mm_prompt_updates:
                filtered_updates = {
                    k: v for k, v in mm_prompt_updates.items() if k != "audio"
                }
                prompt_ids, mm_placeholders = self._apply_prompt_updates(
                    prompt_ids,
                    filtered_updates,
                )
                # Derive audio placeholders from video placeholders
                mm_placeholders = self._derive_audio_from_video_placeholders(
                    mm_placeholders, mm_prompt_updates
                )
            else:
                prompt_ids, mm_placeholders = self._apply_prompt_updates(
                    prompt_ids,
                    mm_prompt_updates,
                )

            self._validate_mm_placeholders(
                mm_placeholders,
                mm_item_counts,
            )

        return prompt_ids, mm_placeholders