def get_ref_info(
            self,
            source: Dict[str, str],
            target_ref_info: Dict[str, Union[str, int]]
    ) -> dict[str, str | int] | None:
        for idx, ref_info in enumerate(source.get("refs", [])) or []:
            if not isinstance(ref_info, dict):
                continue

            ref_index = ref_info.get("ref_index", None)
            ref_type = ref_info.get("ref_type", None)
            if isinstance(ref_index, int) and isinstance(ref_type, str):
                if (not target_ref_info or
                        (target_ref_info["ref_index"] == ref_index and
                         target_ref_info["ref_type"] == ref_type)):
                    return {
                        "ref_index": ref_index,
                        "ref_type": ref_type,
                        "idx": idx
                    }

        return None