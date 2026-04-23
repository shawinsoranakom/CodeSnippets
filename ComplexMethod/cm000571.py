async def run(
        self,
        input_data: Input,
        *,
        credentials: APIKeyCredentials,
        **kwargs,
    ) -> BlockOutput:
        try:
            # Create a new client instance
            pc = Pinecone(api_key=credentials.api_key.get_secret_value())

            # Get the index
            idx = pc.Index(input_data.idx_name)

            # Ensure query_vector is in correct format
            query_vector = input_data.query_vector
            if isinstance(query_vector, list) and len(query_vector) > 0:
                if isinstance(query_vector[0], list):
                    query_vector = query_vector[0]

            results = idx.query(
                namespace=input_data.namespace,
                vector=query_vector,
                top_k=input_data.top_k,
                include_values=input_data.include_values,
                include_metadata=input_data.include_metadata,
            ).to_dict()  # type: ignore
            combined_text = ""
            if results["matches"]:
                texts = [
                    match["metadata"]["text"]
                    for match in results["matches"]
                    if match.get("metadata", {}).get("text")
                ]
                combined_text = "\n\n".join(texts)

            # Return both the raw matches and combined text
            yield "results", {
                "matches": results["matches"],
                "combined_text": combined_text,
            }
            yield "combined_results", combined_text

        except Exception as e:
            error_msg = f"Error querying Pinecone: {str(e)}"
            raise RuntimeError(error_msg) from e