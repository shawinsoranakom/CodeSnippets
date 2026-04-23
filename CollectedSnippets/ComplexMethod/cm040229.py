def _validate_dtype_compatibility(self, teacher, student):
        """Validate that teacher and student have compatible data types."""
        if not hasattr(teacher, "inputs") or not hasattr(student, "inputs"):
            return
        if teacher.inputs is None or student.inputs is None:
            return

        tree.map_structure(
            lambda ti, si: self._assert_same_dtype(ti.dtype, si.dtype, "input"),
            teacher.inputs,
            student.inputs,
        )

        if not hasattr(teacher, "outputs") or not hasattr(student, "outputs"):
            return
        if teacher.outputs is None or student.outputs is None:
            return

        tree.map_structure(
            lambda to, so: self._assert_same_dtype(
                to.dtype, so.dtype, "output"
            ),
            teacher.outputs,
            student.outputs,
        )