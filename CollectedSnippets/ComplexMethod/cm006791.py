def extract_docling_documents(
    data_inputs: Data | list[Data] | DataFrame, doc_key: str
) -> tuple[list[DoclingDocument], str | None]:
    """Extract DoclingDocument objects from data inputs.

    Args:
        data_inputs: The data inputs containing DoclingDocument objects
        doc_key: The key/column name to look for DoclingDocument objects

    Returns:
        A tuple of (documents, warning_message) where warning_message is None if no warning

    Raises:
        TypeError: If the data cannot be extracted or is invalid
    """
    documents: list[DoclingDocument] = []
    warning_message: str | None = None

    if isinstance(data_inputs, DataFrame):
        if not len(data_inputs):
            msg = "DataFrame is empty"
            raise TypeError(msg)

        # Primary: Check for exact column name match
        if doc_key in data_inputs.columns:
            try:
                documents = data_inputs[doc_key].tolist()
            except Exception as e:
                msg = f"Error extracting DoclingDocument from DataFrame column '{doc_key}': {e}"
                raise TypeError(msg) from e
        else:
            # Fallback: Search all columns for DoclingDocument objects
            found_column = None
            for col in data_inputs.columns:
                try:
                    # Check if this column contains DoclingDocument objects
                    sample = data_inputs[col].dropna().iloc[0] if len(data_inputs[col].dropna()) > 0 else None
                    if sample is not None and isinstance(sample, DoclingDocument):
                        found_column = col
                        break
                except (IndexError, AttributeError):
                    continue

            if found_column:
                warning_message = (
                    f"Column '{doc_key}' not found, but found DoclingDocument objects in column '{found_column}'. "
                    f"Using '{found_column}' instead. Consider updating the 'Doc Key' parameter."
                )
                logger.warning(warning_message)
                try:
                    documents = data_inputs[found_column].tolist()
                except Exception as e:
                    msg = f"Error extracting DoclingDocument from DataFrame column '{found_column}': {e}"
                    raise TypeError(msg) from e
            else:
                # Provide helpful error message
                available_columns = list(data_inputs.columns)
                msg = (
                    f"Column '{doc_key}' not found in DataFrame. "
                    f"Available columns: {available_columns}. "
                    f"\n\nPossible solutions:\n"
                    f"1. Use the 'Data' output from Docling component instead of 'DataFrame' output\n"
                    f"2. Update the 'Doc Key' parameter to match one of the available columns\n"
                    f"3. If using VLM pipeline, try using the standard pipeline"
                )
                raise TypeError(msg)
    else:
        if not data_inputs:
            msg = "No data inputs provided"
            raise TypeError(msg)

        if isinstance(data_inputs, Data):
            if doc_key not in data_inputs.data:
                msg = (
                    f"'{doc_key}' field not available in the input Data. "
                    "Check that your input is a DoclingDocument. "
                    "You can use the Docling component to convert your input to a DoclingDocument."
                )
                raise TypeError(msg)
            documents = [data_inputs.data[doc_key]]
        else:
            try:
                documents = [
                    input_.data[doc_key]
                    for input_ in data_inputs
                    if isinstance(input_, Data)
                    and doc_key in input_.data
                    and isinstance(input_.data[doc_key], DoclingDocument)
                ]
                if not documents:
                    msg = f"No valid Data inputs found in {type(data_inputs)}"
                    raise TypeError(msg)
            except AttributeError as e:
                msg = f"Invalid input type in collection: {e}"
                raise TypeError(msg) from e
    return documents, warning_message