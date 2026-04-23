def _get_return_type(self) -> Any:
        return_type = self.return_type
        if inspect.isclass(self.__wrapped__):
            sig_return_type: Any = self.__wrapped__
        else:
            try:
                sig_return_type = inspect.signature(self.__wrapped__).return_annotation
            except ValueError:
                sig_return_type = Any

        try:
            wrapped_sig_return_type = dt.wrap(sig_return_type)
        except TypeError:
            wrapped_sig_return_type = None

        if return_type is not ... and (
            wrapped_sig_return_type is None
            or (
                sig_return_type != Any
                and not dt.dtype_issubclass(
                    wrapped_sig_return_type, dt.wrap(return_type)
                )
            )
        ):
            warn(
                f"The value of return_type parameter ({return_type}) is inconsistent with"
                + f" UDF's return type annotation ({sig_return_type}).",
                stacklevel=3,
            )
        if return_type is ...:  # return type only specified in signature
            if self.max_batch_size is None:
                return sig_return_type
            else:
                if not isinstance(wrapped_sig_return_type, dt.List):
                    raise ValueError(
                        f"A batch UDF has to return a list but is annotated as returning {sig_return_type}"
                    )
                return wrapped_sig_return_type.wrapped

        return return_type