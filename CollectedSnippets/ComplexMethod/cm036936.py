async def test_render_to_generate_roundtrip(client, test_image):
    """End-to-end: render a multimodal chat -> feed into generate -> decode.

    All preprocessing and detokenization happens in the server subprocess;
    the pytest parent never imports transformers or touches torch tensors.
    """
    data_url = encode_image_url(test_image, format="PNG")

    render_payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {
                        "type": "text",
                        "text": "What color is this image? Answer in one word.",
                    },
                ],
            }
        ],
    }

    render_resp = await client.post(RENDER_ENDPOINT, json=render_payload)
    render_resp.raise_for_status()
    render_data = render_resp.json()

    # Validate render output structure: keys exist and values are non-empty
    # and well-typed.
    assert "token_ids" in render_data
    assert isinstance(render_data["token_ids"], list)
    assert len(render_data["token_ids"]) > 0
    assert all(isinstance(t, int) for t in render_data["token_ids"])

    assert "features" in render_data
    features = render_data["features"]
    assert features is not None
    assert isinstance(features, dict)

    assert "mm_hashes" in features
    assert "image" in features["mm_hashes"]
    image_hashes = features["mm_hashes"]["image"]
    assert isinstance(image_hashes, list)
    assert len(image_hashes) > 0
    assert all(isinstance(h, str) and h for h in image_hashes)

    assert "mm_placeholders" in features
    assert "image" in features["mm_placeholders"]
    image_placeholders = features["mm_placeholders"]["image"]
    assert isinstance(image_placeholders, list)
    assert len(image_placeholders) > 0
    for p in image_placeholders:
        assert isinstance(p.get("offset"), int)
        assert isinstance(p.get("length"), int)
        assert p["length"] > 0

    assert "kwargs_data" in features
    assert "image" in features["kwargs_data"]
    assert len(features["kwargs_data"]["image"]) > 0

    # Build generate request from render output
    generate_payload = render_data
    generate_payload["sampling_params"] = {
        "max_tokens": 10,
        "temperature": 0.0,
    }

    gen_resp = await client.post(GEN_ENDPOINT, json=generate_payload)
    gen_resp.raise_for_status()
    gen_data = gen_resp.json()

    assert "choices" in gen_data
    assert isinstance(gen_data["choices"], list)
    assert len(gen_data["choices"]) >= 1
    choice = gen_data["choices"][0]
    assert "token_ids" in choice
    assert isinstance(choice["token_ids"], list)
    assert len(choice["token_ids"]) > 0
    assert all(isinstance(t, int) for t in choice["token_ids"])

    detok_resp = await client.post(
        DETOKENIZE_ENDPOINT,
        json={"model": MODEL_NAME, "tokens": choice["token_ids"]},
    )
    detok_resp.raise_for_status()
    detok_data = detok_resp.json()
    assert "prompt" in detok_data
    text = detok_data["prompt"]
    assert isinstance(text, str)
    assert len(text) > 0
    assert "red" in text.lower(), (
        f"Expected model to identify the red image, got: {text!r}"
    )