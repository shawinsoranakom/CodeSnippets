async def test_copy_profile_pictures_source_exists():
    """Test that the source profile pictures directory exists in the package."""
    from langflow.initial_setup import setup

    source_path = Path(setup.__file__).parent / "profile_pictures"
    assert await source_path.exists(), "Source profile_pictures directory should exist in package"

    people_source = source_path / "People"
    space_source = source_path / "Space"

    assert await people_source.exists(), "Source People directory should exist"
    assert await space_source.exists(), "Source Space directory should exist"

    # Count source files
    people_files = [f async for f in people_source.glob("*.svg")]
    space_files = [f async for f in space_source.glob("*.svg")]

    assert len(people_files) > 0, "Source should have People profile pictures"
    assert len(space_files) > 0, "Source should have Space profile pictures"