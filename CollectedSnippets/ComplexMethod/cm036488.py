def check_transformers_version(
        self,
        *,
        on_fail: Literal["error", "skip", "return"],
        check_version_reason: Literal["vllm", "hf"] = "hf",
        check_min_version: bool = True,
        check_max_version: bool = True,
    ) -> str | None:
        """
        If the installed transformers version does not meet the requirements,
        perform the given action.
        """
        if (
            self.min_transformers_version is None
            and self.max_transformers_version is None
        ):
            return None

        current_version = TRANSFORMERS_VERSION
        cur_base_version = Version(current_version).base_version
        min_version = self.min_transformers_version
        max_version = self.max_transformers_version
        msg = f"`transformers=={current_version}` installed, but `transformers"
        # Only check the base version for the min/max version, otherwise preview
        # models cannot be run because `x.yy.0.dev0`<`x.yy.0`
        if min_version and Version(cur_base_version) < Version(min_version):
            is_version_valid = not check_min_version
            msg += f">={min_version}` is required to run this model."
        elif max_version and Version(cur_base_version) > Version(max_version):
            is_version_valid = not check_max_version
            msg += f"<={max_version}` is required to run this model."
        else:
            is_version_valid = True

        # check if Transformers version breaks the corresponding model runner,
        # skip test when model runner not compatible
        is_reason_valid = not (
            check_version_reason
            and self.transformers_version_reason
            and check_version_reason in self.transformers_version_reason
        )
        is_transformers_valid = is_version_valid and is_reason_valid
        if is_transformers_valid:
            return None
        elif self.transformers_version_reason:
            for reason_type, reason in self.transformers_version_reason.items():
                msg += f" Reason({reason_type}): {reason}"

        if on_fail == "error":
            raise RuntimeError(msg)
        elif on_fail == "skip":
            pytest.skip(msg)

        return msg