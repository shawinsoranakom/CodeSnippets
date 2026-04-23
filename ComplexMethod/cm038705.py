def validate_offload_config(self) -> "OffloadConfig":
        """Validate offload configuration constraints."""
        if self.offload_backend == "prefetch" or self.prefetch.offload_group_size > 0:
            if self.prefetch.offload_num_in_group > self.prefetch.offload_group_size:
                raise ValueError(
                    f"offload_num_in_group ({self.prefetch.offload_num_in_group})"
                    f" must be <= offload_group_size"
                    f" ({self.prefetch.offload_group_size})"
                )
            if self.prefetch.offload_prefetch_step < 1:
                raise ValueError(
                    f"offload_prefetch_step"
                    f" ({self.prefetch.offload_prefetch_step})"
                    f" must be >= 1 when prefetch offloading is enabled"
                    f" (offload_group_size > 0)"
                )

        # Warn if both backends have non-default values
        uva_active = self.uva.cpu_offload_gb > 0
        prefetch_active = self.prefetch.offload_group_size > 0
        if self.offload_backend == "uva" and prefetch_active:
            warnings.warn(
                "Prefetch offload fields are set but offload_backend='uva'. "
                "Prefetch settings will be ignored.",
                stacklevel=2,
            )
        elif self.offload_backend == "prefetch" and uva_active:
            warnings.warn(
                "UVA offload fields are set but offload_backend='prefetch'. "
                "UVA settings will be ignored.",
                stacklevel=2,
            )
        elif self.offload_backend == "auto" and uva_active and prefetch_active:
            warnings.warn(
                "Both UVA and prefetch offload fields are set with "
                "offload_backend='auto'. Prefetch backend will be selected. "
                "Set offload_backend explicitly to suppress this warning.",
                stacklevel=2,
            )
        return self