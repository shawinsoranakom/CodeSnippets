async def _agenerate_rest_batches(
        self,
        texts: Iterable[str],
        metadatas: list[dict] | None = None,
        ids: Sequence[str] | None = None,
        batch_size: int = 64,
    ) -> AsyncGenerator[tuple[list[str], list[models.PointStruct]], None]:
        texts_iterator = iter(texts)
        metadatas_iterator = iter(metadatas or [])
        ids_iterator = iter(ids or [uuid.uuid4().hex for _ in iter(texts)])
        while batch_texts := list(islice(texts_iterator, batch_size)):
            # Take the corresponding metadata and id for each text in a batch
            batch_metadatas = list(islice(metadatas_iterator, batch_size)) or None
            batch_ids = list(islice(ids_iterator, batch_size))

            # Generate the embeddings for all the texts in a batch
            batch_embeddings = await self._aembed_texts(batch_texts)

            points = [
                models.PointStruct(
                    id=point_id,
                    vector=vector  # type: ignore[arg-type]
                    if self.vector_name is None
                    else {self.vector_name: vector},
                    payload=payload,
                )
                for point_id, vector, payload in zip(
                    batch_ids,
                    batch_embeddings,
                    self._build_payloads(
                        batch_texts,
                        batch_metadatas,
                        self.content_payload_key,
                        self.metadata_payload_key,
                    ),
                    strict=False,
                )
            ]

            yield batch_ids, points