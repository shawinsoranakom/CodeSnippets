def get_fomc_documents_by_year(
    year: int | None = None,
    document_type: FomcDocumentType | None = None,
    pdf_only: bool = False,
) -> list[dict]:
    """
    Get a list of FOMC documents by year and document type.

    Parameters
    ----------
    year : Optional[int]
        The year of the FOMC documents to retrieve. If None, all years since 1959 are returned.
    document_type : Optional[FomcDocumentType]
        The type of FOMC document to retrieve. If None, all document types are returned.
        Valid document types are:
        - all
        - monetary_policy
        - minutes
        - projections
        - materials
        - press_release
        - press_conference
        - conference_call
        - agenda
        - transcript
        - speaker_key
        - beige_book
        - teal_book
        - green_book
        - blue_book
        - red_book
    pdf_only : bool
        Whether to return with only the PDF documents. Default is False.

    Returns
    -------
    list[dict]
        A list of dictionaries mapping FOMC documents to URLs.
        Each dictionary contains the following:
        - date: str
            The date of the document, formatted as YYYY-MM-DD.
        - doc_type: str
            The type of the document.
        - doc_format: str
            The format of the document.
        - url: str
            The URL of the document
    """
    filtered_docs: list[dict] = []
    choice_types = list(getattr(FomcDocumentType, "__args__", ()))

    if year and year < 1959:
        raise ValueError("Year must be from 1959.")

    if year and isinstance(year, str):
        year = int(year) if year.isdigit() else 0
        if year == 0:
            raise ValueError("Year must be an integer.")

    if not document_type:
        document_type = "all"

    if document_type not in choice_types:
        raise ValueError(
            f"Invalid document type. Must be one of: {', '.join(choice_types)}"
        )

    if year:
        docs = (
            get_current_fomc_documents()
            if year > 2024
            else load_historical_fomc_documents()
        )
    else:
        current_docs = get_current_fomc_documents()
        historical_docs = load_historical_fomc_documents()
        docs = current_docs + historical_docs

    for doc in docs:
        doc_year = int(doc["date"].split("-")[0])
        if year and doc_year != year:
            continue
        if pdf_only is True and doc["doc_format"] != "pdf":
            continue
        if document_type in ("all", doc["doc_type"]):
            filtered_docs.append(doc)

    return sorted(filtered_docs, key=lambda x: x["date"], reverse=True)