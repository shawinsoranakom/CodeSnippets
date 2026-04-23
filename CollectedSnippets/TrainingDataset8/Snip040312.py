def _patch_local_sources_watcher():
    """Return a mock.patch for LocalSourcesWatcher"""
    return patch("streamlit.runtime.runtime.LocalSourcesWatcher")