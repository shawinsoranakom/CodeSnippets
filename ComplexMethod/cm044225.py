def test(
        cls,
        params: dict[str, Any],
        credentials: dict[str, str] | None = None,
        **kwargs,
    ) -> None:
        """Test the fetcher.

        This method will test each stage of the fetcher TET (Transform, Extract, Transform).

        Parameters
        ----------
        params : Dict[str, Any]
            The params to test the fetcher with.
        credentials : Optional[Dict[str, str]], optional
            The credentials to test the fetcher with, by default None.

        Raises
        ------
        AssertionError
            If any of the tests fail.
        """
        # pylint: disable=import-outside-toplevel
        from pandas import DataFrame

        query = cls.transform_query(params=params)
        data = run_async(
            cls.extract_data, query=query, credentials=credentials, **kwargs
        )
        result = cls.transform_data(query=query, data=data, **kwargs)

        # Class Assertions
        assert isinstance(
            cls.require_credentials, bool
        ), "require_credentials must be a boolean."

        # Query Assertions
        assert query, "Query must not be None."
        assert issubclass(
            type(query), cls.query_params_type
        ), f"Query type mismatch. Expected: {cls.query_params_type} Got: {type(query)}"
        assert all(
            getattr(query, key) == value for key, value in params.items()
        ), f"Query must have the correct values. Expected: {params} Got: {query.__dict__}"

        # Data Assertions
        if not isinstance(data, DataFrame):
            assert data, "Data must not be None."
        else:
            assert not data.empty, "Data must not be empty."
        is_list = isinstance(data, list)
        if is_list:
            assert all(
                field in data[0]
                for field in cls.data_type.model_fields
                if field in data[0]
            ), f"Data must have the correct fields. Expected: {cls.data_type.model_fields} Got: {data[0].__dict__}"
            # This makes sure that the data is not transformed yet so that the
            # pipeline is implemented correctly. We can remove this assertion if we
            # want to be less strict.
            assert (
                issubclass(type(data[0]), cls.data_type) is False
            ), f"Data must not be transformed yet. Expected: {cls.data_type} Got: {type(data[0])}"
        else:
            assert all(
                field in data for field in cls.data_type.model_fields if field in data
            ), f"Data must have the correct fields. Expected: {cls.data_type.model_fields} Got: {data.__dict__}"
            assert (
                issubclass(type(data), cls.data_type) is False
            ), f"Data must not be transformed yet. Expected: {cls.data_type} Got: {type(data)}"

        assert len(data) > 0, "Data must not be empty."

        # Transformed Data Assertions
        transformed_data = (
            result.result if isinstance(result, AnnotatedResult) else result
        )

        assert transformed_data, "Transformed data must not be None."

        if isinstance(transformed_data, list):
            return_type_args = cls.return_type.__args__[0]
            return_type_is_dict = (
                hasattr(return_type_args, "__origin__")
                and return_type_args.__origin__ is dict
            )
            if return_type_is_dict:
                return_type_fields = (
                    return_type_args.__args__[1].__args__[0].model_fields
                )
                return_type = return_type_args.__args__[1].__args__[0]
            else:
                return_type_fields = return_type_args.model_fields
                return_type = return_type_args

            assert len(transformed_data) > 0, "Transformed data must not be empty."  # type: ignore
            assert all(
                field in transformed_data[0].__dict__ for field in return_type_fields  # type: ignore
            ), f"Transformed data must have the correct fields. Expected: {return_type_fields} Got: {transformed_data[0].__dict__}"  # type: ignore
            assert issubclass(
                type(transformed_data[0]),
                cls.data_type,  # type: ignore
            ), f"Transformed data must be of the correct type. Expected: {cls.data_type} Got: {type(transformed_data[0])}"  # type: ignore
            assert issubclass(  # type: ignore
                type(transformed_data[0]),  # type: ignore
                return_type,
            ), f"Transformed data must be of the correct type. Expected: {return_type} Got: {type(transformed_data[0])}"  # type: ignore
        else:
            assert all(
                field in transformed_data.__dict__
                for field in cls.return_type.model_fields
            ), f"Transformed data must have the correct fields. Expected: {cls.return_type.model_fields} Got: {transformed_data.__dict__}"
            assert issubclass(
                type(transformed_data), cls.data_type
            ), f"Transformed data must be of the correct type. Expected: {cls.data_type} Got: {type(transformed_data)}"
            assert issubclass(
                type(transformed_data), cls.return_type
            ), f"Transformed data must be of the correct type. Expected: {cls.return_type} Got: {type(transformed_data)}"