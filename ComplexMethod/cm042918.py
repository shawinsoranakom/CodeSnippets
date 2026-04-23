def test_deep_crawl_markdown_output_includes_all_pages(self, runner, mock_crawl_results):
        """Test that deep crawl with markdown output includes all pages, not just the first"""
        with patch('crawl4ai.cli.anyio.run') as mock_anyio_run:
            # Return list of results (simulating deep crawl)
            mock_anyio_run.return_value = mock_crawl_results

            result = runner.invoke(cli, [
                'crawl',
                'https://example.com',
                '--deep-crawl', 'bfs',
                '--max-pages', '3',
                '-o', 'markdown'
            ])

            assert result.exit_code == 0, f"CLI failed with: {result.output}"
            # Should contain content from ALL pages
            assert 'https://example.com/' in result.output
            assert 'https://example.com/about' in result.output
            assert 'https://example.com/contact' in result.output
            assert 'Homepage' in result.output
            assert 'About us page content' in result.output
            assert 'Contact information' in result.output