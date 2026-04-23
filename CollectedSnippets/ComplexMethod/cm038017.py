def _calc_context_sizes(
        self,
        att_context_size: list[int] | list[list[int]] | None,
        att_context_probs: list[float] | None,
        att_context_style: str,
        conv_context_size: list[int] | str | None,
        conv_kernel_size: int,
    ) -> tuple[list[list[int]], list[int], list[float], list[int]]:
        # convert att_context_size to a standard list of lists
        if att_context_size:
            att_context_size_all = list(att_context_size)
            if isinstance(att_context_size_all[0], int):
                att_context_size_all = [att_context_size_all]
            for i, att_cs in enumerate(att_context_size_all):
                if att_context_style == "chunked_limited":
                    if att_cs[0] > 0 and att_cs[0] % (att_cs[1] + 1) > 0:
                        raise ValueError(
                            f"att_context_size[{i}][0] % "
                            f"(att_context_size[{i}][1]"
                            f" + 1) should be zero!"
                        )
                    if att_cs[1] < 0 and len(att_context_size_all) <= 1:
                        raise ValueError(
                            f"Right context "
                            f"(att_context_size[{i}][1])"
                            f" can not be unlimited for"
                            f" chunked_limited style!"
                        )
        else:
            att_context_size_all = [[-1, -1]]

        if att_context_probs:
            if len(att_context_probs) != len(att_context_size_all):
                raise ValueError(
                    "The size of the att_context_probs "
                    "should be the same as att_context_size."
                )
            att_context_probs = list(att_context_probs)
            if sum(att_context_probs) != 1:
                raise ValueError(
                    "The sum of numbers in "
                    "att_context_probs should be equal "
                    "to one to be a distribution."
                )
        else:
            att_context_probs = [1.0 / len(att_context_size_all)] * len(
                att_context_size_all
            )

        if conv_context_size is not None:
            if not isinstance(conv_context_size, list) and not isinstance(
                conv_context_size, str
            ):
                raise ValueError(
                    "Invalid conv_context_size! It should "
                    "be the string 'causal' or a list of "
                    "two integers."
                )
            if conv_context_size == "causal":
                conv_context_size = [conv_kernel_size - 1, 0]
            else:
                total = conv_context_size[0] + conv_context_size[1] + 1
                if total != conv_kernel_size:
                    raise ValueError(
                        f"Invalid conv_context_size: {self.conv_context_size}!"
                    )
        else:
            conv_context_size = [
                (conv_kernel_size - 1) // 2,
                (conv_kernel_size - 1) // 2,
            ]
        return (
            att_context_size_all,
            att_context_size_all[0],
            att_context_probs,
            conv_context_size,
        )