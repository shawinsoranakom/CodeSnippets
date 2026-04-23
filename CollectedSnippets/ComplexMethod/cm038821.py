def _set_adapter_mapping(self, mapping: LoRAMapping) -> None:
        # Default to the main language model wrapper
        if not (self.supports_mm and self.supports_tower_connector_lora):
            target_prefix = (
                self.mm_mapping.language_model[0]
                if self.supports_mm
                else DEFAULT_LANGUAGE_WRAPPER_KEY
            )
        elif mapping.type == LoRAMappingType.TOWER and self.mm_mapping.tower_model:
            target_prefix = self.mm_mapping.tower_model[0]
        elif mapping.type == LoRAMappingType.CONNECTOR and self.mm_mapping.connector:
            target_prefix = self.mm_mapping.connector[0]
        else:
            target_prefix = self.mm_mapping.language_model[0]

        punica_wrapper = self._get_punica_wrapper(target_prefix)
        assert punica_wrapper is not None

        punica_wrapper.update_metadata(
            mapping,
            self.lora_index_to_id,
            self.lora_slots + 1,
            self.vocab_size,
        )