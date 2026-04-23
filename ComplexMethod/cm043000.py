async def _test():
            srv = _TestServer()
            await srv.start()
            try:
                dl_dir = str(tmp_path / "dl")
                os.makedirs(dl_dir)
                result = await _crawl(srv, "/data.csv", dl_dir)

                assert result.downloaded_files is not None
                assert len(result.downloaded_files) == 1
                filepath = result.downloaded_files[0]
                assert filepath.endswith("data.csv")
                assert os.path.isfile(filepath)
                assert "alpha" in result.html
                assert "id,name,value" in result.html
                with open(filepath) as f:
                    assert "alpha" in f.read()
            finally:
                await srv.stop()