def extractor():
            comments = []
            interrupted = True
            try:
                while True:
                    comments.append(next(generator))
            except StopIteration:
                interrupted = False
            except KeyboardInterrupt:
                self.to_screen('Interrupted by user')
            except self.CommentsDisabled:
                return {'comments': None, 'comment_count': None}
            except Exception as e:
                if self.get_param('ignoreerrors') is not True:
                    raise
                self._downloader.report_error(e)
            comment_count = len(comments)
            self.to_screen(f'Extracted {comment_count} comments')
            return {
                'comments': comments,
                'comment_count': None if interrupted else comment_count,
            }