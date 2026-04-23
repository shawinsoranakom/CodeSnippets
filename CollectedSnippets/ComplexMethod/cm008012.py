def __extract_info(self, url, ie, download, extra_info, process):
        self._apply_header_cookies(url)

        try:
            ie_result = ie.extract(url)
        except UserNotLive as e:
            if process:
                if self.params.get('wait_for_video'):
                    self.report_warning(e)
                self._wait_for_video()
            raise
        if ie_result is None:  # Finished already (backwards compatibility; listformats and friends should be moved here)
            self.report_warning(f'Extractor {ie.IE_NAME} returned nothing{bug_reports_message()}')
            return
        if isinstance(ie_result, list):
            # Backwards compatibility: old IE result format
            ie_result = {
                '_type': 'compat_list',
                'entries': ie_result,
            }
        if extra_info.get('original_url'):
            ie_result.setdefault('original_url', extra_info['original_url'])
        self.add_default_extra_info(ie_result, ie, url)
        if process:
            self._wait_for_video(ie_result)
            return self.process_ie_result(ie_result, download, extra_info)
        else:
            return ie_result