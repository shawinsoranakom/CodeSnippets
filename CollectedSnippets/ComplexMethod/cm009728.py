def test_tracer_metadata_not_applied_to_sibling_handlers(self) -> None:
        """Tracer metadata is not applied to other callback handlers.

        `_patch_missing_metadata` copies the metadata dict before patching,
        so the callback manager's shared metadata dict is not mutated.
        Other handlers should only see config metadata, not tracer metadata.
        """
        tracer = _create_tracer_with_mocked_client(
            metadata={"tracer_key": "tracer_val"}
        )

        received_metadata: list[dict[str, Any]] = []

        class MetadataCapture(BaseCallbackHandler):
            """Callback handler that records metadata from chain events."""

            def on_chain_start(self, *_args: Any, **kwargs: Any) -> None:
                received_metadata.append(dict(kwargs.get("metadata", {})))

        capture = MetadataCapture()

        @RunnableLambda
        def my_func(x: int) -> int:
            return x

        my_func.invoke(
            1,
            {
                "callbacks": [tracer, capture],
                "metadata": {"shared_key": "shared_val"},
            },
        )

        assert len(received_metadata) >= 1
        for md in received_metadata:
            assert md["shared_key"] == "shared_val"
            assert "tracer_key" not in md

        # But the posted run DOES have tracer metadata
        posts = _get_posts(tracer.client)
        assert len(posts) >= 1
        for post in posts:
            post_md = post.get("extra", {}).get("metadata", {})
            assert post_md["shared_key"] == "shared_val"
            assert post_md["tracer_key"] == "tracer_val"