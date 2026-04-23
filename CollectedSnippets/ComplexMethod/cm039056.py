def _get_fitted_attr_html(self, doc_link=""):
        """Get fitted attributes of the estimator."""

        fitted_attr = {}
        for name, value in inspect.getmembers(self):
            # We display up to 100 fitted attributes
            if len(fitted_attr) > 100:
                fitted_attr["..."] = {
                    "type_name": "...",
                    "value": "",
                }
                break
            if name.startswith("_") or not name.endswith("_"):
                continue
            if (
                hasattr(value, "shape")
                and hasattr(value, "dtype")
                and not isinstance(value, numbers.Number)
            ):
                # array-like attribute with shape and dtype
                fitted_attr[name] = {
                    "type_name": type(value).__name__,
                    "shape": value.shape,
                    "dtype": value.dtype,
                    "value": value,
                }
            else:
                fitted_attr[name] = {
                    "type_name": type(value).__name__,
                    "value": value,
                }

        return AttrsDict(
            fitted_attrs=fitted_attr,
            estimator_class=self.__class__,
            doc_link=doc_link,
        )