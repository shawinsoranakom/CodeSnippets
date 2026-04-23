def test_apply_patch_rename_directory(mock_output_dir):
    # Create a sample directory structure
    old_dir = os.path.join(mock_output_dir, 'prompts', 'resolve')
    os.makedirs(old_dir)

    # Create test files
    test_files = [
        'issue-success-check.jinja',
        'pr-feedback-check.jinja',
        'pr-thread-check.jinja',
    ]
    for filename in test_files:
        file_path = os.path.join(old_dir, filename)
        with open(file_path, 'w') as f:
            f.write(f'Content of {filename}')

    # Create a patch that renames the directory
    patch_content = """diff --git a/prompts/resolve/issue-success-check.jinja b/prompts/guess_success/issue-success-check.jinja
similarity index 100%
rename from prompts/resolve/issue-success-check.jinja
rename to prompts/guess_success/issue-success-check.jinja
diff --git a/prompts/resolve/pr-feedback-check.jinja b/prompts/guess_success/pr-feedback-check.jinja
similarity index 100%
rename from prompts/resolve/pr-feedback-check.jinja
rename to prompts/guess_success/pr-feedback-check.jinja
diff --git a/prompts/resolve/pr-thread-check.jinja b/prompts/guess_success/pr-thread-check.jinja
similarity index 100%
rename from prompts/resolve/pr-thread-check.jinja
rename to prompts/guess_success/pr-thread-check.jinja"""

    # Apply the patch
    apply_patch(mock_output_dir, patch_content)

    # Check if files were moved correctly
    new_dir = os.path.join(mock_output_dir, 'prompts', 'guess_success')
    assert not os.path.exists(old_dir), 'Old directory still exists'
    assert os.path.exists(new_dir), 'New directory was not created'

    # Check if all files were moved and content preserved
    for filename in test_files:
        old_path = os.path.join(old_dir, filename)
        new_path = os.path.join(new_dir, filename)
        assert not os.path.exists(old_path), f'Old file {filename} still exists'
        assert os.path.exists(new_path), f'New file {filename} was not created'
        with open(new_path, 'r') as f:
            content = f.read()
        assert content == f'Content of {filename}', f'Content mismatch for {filename}'