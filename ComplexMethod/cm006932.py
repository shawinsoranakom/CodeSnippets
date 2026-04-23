def generate_embeddings(self) -> Data:
        try:
            embedding_model: Embeddings = self.embedding_model
            message: Message = self.message

            # Combine validation checks to reduce nesting
            if not embedding_model or not hasattr(embedding_model, "embed_documents"):
                msg = "Invalid or incompatible embedding model"
                raise ValueError(msg)

            text_content = message.text if message and message.text else ""
            if not text_content:
                msg = "No text content found in message"
                raise ValueError(msg)

            embeddings = embedding_model.embed_documents([text_content])
            if not embeddings or not isinstance(embeddings, list):
                msg = "Invalid embeddings generated"
                raise ValueError(msg)

            embedding_vector = embeddings[0]
            self.status = {"text": text_content, "embeddings": embedding_vector}
            return Data(data={"text": text_content, "embeddings": embedding_vector})
        except Exception as e:  # noqa: BLE001
            logger.exception("Error generating embeddings")
            error_data = Data(data={"text": "", "embeddings": [], "error": str(e)})
            self.status = {"error": str(e)}
            return error_data