def _can_tile_ax(ax: int, dim: int, t: int) -> bool:
        """Check if tiling dim to t is valid."""
        if t >= dim:
            # For TPU padding, we allow tiles >= dimension for the aligned axes
            if _align(ax) == _TPU_ALIGN_LAST or _align(ax) == _TPU_ALIGN_SECOND_LAST:
                return True
            return False
        if exact_only and dim % t != 0:
            if _align(ax) == _TPU_ALIGN_LAST or _align(ax) == _TPU_ALIGN_SECOND_LAST:
                # TPU DMA `#tpu.element_window` natively masks out-of-bounds remainder tiles
                return True
            return False
        return True