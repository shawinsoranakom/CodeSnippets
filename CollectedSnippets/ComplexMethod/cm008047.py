def _write_link_file(link_type):
            url = try_get(info_dict['webpage_url'], iri_to_uri)
            if not url:
                self.report_warning(
                    f'Cannot write internet shortcut file because the actual URL of "{info_dict["webpage_url"]}" is unknown')
                return True
            linkfn = replace_extension(self.prepare_filename(info_dict, 'link'), link_type, info_dict.get('ext'))
            if not self._ensure_dir_exists(linkfn):
                return False
            if self.params.get('overwrites', True) and os.path.exists(linkfn):
                self.to_screen(f'[info] Internet shortcut (.{link_type}) is already present')
                return True
            try:
                self.to_screen(f'[info] Writing internet shortcut (.{link_type}) to: {linkfn}')
                with open(to_high_limit_path(linkfn), 'w', encoding='utf-8',
                          newline='\r\n' if link_type == 'url' else '\n') as linkfile:
                    template_vars = {'url': url}
                    if link_type == 'desktop':
                        template_vars['filename'] = linkfn[:-(len(link_type) + 1)]
                    linkfile.write(LINK_TEMPLATES[link_type] % template_vars)
            except OSError:
                self.report_error(f'Cannot write internet shortcut {linkfn}')
                return False
            return True