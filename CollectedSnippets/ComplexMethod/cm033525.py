def test_rename_perms_fail_temp_succeeds(atomic_am, atomic_mocks, fake_stat, mocker, selinux):
    """Test os.rename raising an error but fallback to using mkstemp works"""
    mock_context = atomic_am.selinux_default_context.return_value
    atomic_mocks['path_exists'].return_value = False
    atomic_mocks['rename'].side_effect = [OSError(errno.EPERM, 'failing with EPERM'), None]
    atomic_mocks['mkstemp'].return_value = (None, '/path/to/tempfile')
    atomic_mocks['mkstemp'].side_effect = None
    atomic_am.selinux_enabled.return_value = selinux

    atomic_am.atomic_move('/path/to/src', '/path/to/dest')
    assert atomic_mocks['rename'].call_args_list == [mocker.call(b'/path/to/src', b'/path/to/dest'),
                                                     mocker.call(b'/path/to/tempfile', b'/path/to/dest')]
    assert atomic_mocks['chmod'].call_args_list == [mocker.call(b'/path/to/dest', basic.DEFAULT_PERM & ~18)]

    if selinux:
        assert atomic_am.selinux_default_context.call_args_list == [mocker.call('/path/to/dest')]
        assert atomic_am.set_context_if_different.call_args_list == [mocker.call(b'/path/to/tempfile', mock_context, False),
                                                                     mocker.call('/path/to/dest', mock_context, False)]
    else:
        assert not atomic_am.selinux_default_context.called
        assert not atomic_am.set_context_if_different.called