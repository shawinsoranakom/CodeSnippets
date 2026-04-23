def _crawl_result_to_export_dict(self, result) -> Dict[str, Any]:
        """Convert CrawlResult to a dictionary for export"""
        # Extract all available fields
        export_dict = {
            'url': getattr(result, 'url', ''),
            'timestamp': getattr(result, 'timestamp', None),
            'success': getattr(result, 'success', True),
            'query': self.state.query if self.state else '',
        }

        # Extract content
        if hasattr(result, 'markdown') and result.markdown:
            if hasattr(result.markdown, 'raw_markdown'):
                export_dict['content'] = result.markdown.raw_markdown
            else:
                export_dict['content'] = str(result.markdown)
        else:
            export_dict['content'] = ''

        # Extract metadata
        if hasattr(result, 'metadata'):
            export_dict['metadata'] = result.metadata

        # Extract links if available
        if hasattr(result, 'links'):
            export_dict['links'] = result.links

        # Add crawl-specific metadata
        if self.state:
            export_dict['crawl_metadata'] = {
                'crawl_order': self.state.crawl_order.index(export_dict['url']) + 1 if export_dict['url'] in self.state.crawl_order else 0,
                'confidence_at_crawl': self.state.metrics.get('confidence', 0),
                'total_documents': self.state.total_documents
            }

        return export_dict