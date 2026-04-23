def run(self, checkpoint: CT) -> Generator[
        tuple[list[Document] | None, ConnectorFailure | None, CT | None],
        None,
        None,
    ]:
        """Adds additional exception logging to the connector."""
        try:
            if isinstance(self.connector, CheckpointedConnector):
                if self.time_range is None:
                    raise ValueError("time_range is required for CheckpointedConnector")

                start = time.monotonic()
                if self.include_permissions:
                    if not isinstance(
                        self.connector, CheckpointedConnectorWithPermSync
                    ):
                        raise ValueError(
                            "Connector does not support permission syncing"
                        )
                    load_from_checkpoint = (
                        self.connector.load_from_checkpoint_with_perm_sync
                    )
                else:
                    load_from_checkpoint = self.connector.load_from_checkpoint
                checkpoint_connector_generator = load_from_checkpoint(
                    start=self.time_range[0].timestamp(),
                    end=self.time_range[1].timestamp(),
                    checkpoint=checkpoint,
                )
                next_checkpoint: CT | None = None
                # this is guaranteed to always run at least once with next_checkpoint being non-None
                for document, failure, next_checkpoint in CheckpointOutputWrapper[CT]()(
                    checkpoint_connector_generator
                ):
                    if document is not None and isinstance(document, Document):
                        self.doc_batch.append(document)

                    if failure is not None:
                        yield None, failure, None

                    if len(self.doc_batch) >= self.batch_size:
                        yield self.doc_batch, None, None
                        self.doc_batch = []

                # yield remaining documents
                if len(self.doc_batch) > 0:
                    yield self.doc_batch, None, None
                    self.doc_batch = []

                yield None, None, next_checkpoint

                logging.debug(
                    f"Connector took {time.monotonic() - start} seconds to get to the next checkpoint."
                )

            else:
                finished_checkpoint = self.connector.build_dummy_checkpoint()
                finished_checkpoint.has_more = False

                if isinstance(self.connector, PollConnector):
                    if self.time_range is None:
                        raise ValueError("time_range is required for PollConnector")

                    for document_batch in self.connector.poll_source(
                        start=self.time_range[0].timestamp(),
                        end=self.time_range[1].timestamp(),
                    ):
                        yield document_batch, None, None

                    yield None, None, finished_checkpoint
                elif isinstance(self.connector, LoadConnector):
                    for document_batch in self.connector.load_from_state():
                        yield document_batch, None, None

                    yield None, None, finished_checkpoint
                else:
                    raise ValueError(f"Invalid connector. type: {type(self.connector)}")
        except Exception:
            exc_type, _, exc_traceback = sys.exc_info()

            # Traverse the traceback to find the last frame where the exception was raised
            tb = exc_traceback
            if tb is None:
                logging.error("No traceback found for exception")
                raise

            while tb.tb_next:
                tb = tb.tb_next  # Move to the next frame in the traceback

            # Get the local variables from the frame where the exception occurred
            local_vars = tb.tb_frame.f_locals
            local_vars_str = "\n".join(
                f"{key}: {value}" for key, value in local_vars.items()
            )
            logging.error(
                f"Error in connector. type: {exc_type};\n"
                f"local_vars below -> \n{local_vars_str[:1024]}"
            )
            raise