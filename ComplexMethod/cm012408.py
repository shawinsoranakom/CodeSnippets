def _is_valid_dtype_combo(ab_dtype, sf_dtype, sf_vec_size, out_dtype) -> bool:
        """Validate dtype/scale-factor/vec-size combinations.

        Matches constraints from the upstream kernel:
          MXF8: Float8E5M2/Float8E4M3FN + Float8E8M0FNU, sf_vec_size=32
          MXF4: Float4E2M1FN + Float8E8M0FNU, sf_vec_size=32
          NVF4: Float4E2M1FN + Float8E8M0FNU/Float8E4M3FN, sf_vec_size=16
        """
        import cutlass

        if ab_dtype not in {
            cutlass.Float4E2M1FN,
            cutlass.Float8E5M2,
            cutlass.Float8E4M3FN,
        }:
            return False
        if sf_vec_size not in {16, 32}:
            return False
        if sf_dtype not in {cutlass.Float8E8M0FNU, cutlass.Float8E4M3FN}:
            return False
        # Float8E4M3FN as SF only valid with sf_vec_size=16 (NVF4)
        if sf_dtype == cutlass.Float8E4M3FN and sf_vec_size == 32:
            return False
        # Float8 AB types require sf_vec_size=32 (MXF8)
        if ab_dtype in {cutlass.Float8E5M2, cutlass.Float8E4M3FN} and sf_vec_size == 16:
            return False
        if out_dtype not in {
            cutlass.Float32,
            cutlass.Float16,
            cutlass.BFloat16,
            cutlass.Float8E5M2,
            cutlass.Float8E4M3FN,
        }:
            return False
        return True