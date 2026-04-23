def get_reference(self, ref_info: Dict[str, Union[str, int]]) -> Any:
        for reference in self.list:
            reference_ref_info = self.get_ref_info(reference, ref_info)

            if (not reference_ref_info or
                    reference_ref_info["ref_index"] != ref_info["ref_index"] or
                    reference_ref_info["ref_type"] != ref_info["ref_type"]):
                continue

            if ref_info["ref_type"] != "image":
                return reference

            images = reference.get("images", [])
            if isinstance(images, list) and len(images) > reference_ref_info["idx"]:
                return images[reference_ref_info["idx"]]

        return None