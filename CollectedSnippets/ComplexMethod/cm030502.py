def render_hierarchical_html(self, trees: Dict[str, TreeNode]) -> str:
        """Build hierarchical HTML with type sections and collapsible module folders.

        Args:
            trees: Dictionary mapping module types to tree roots

        Returns:
            Complete HTML string for all sections
        """
        type_names = {
            'stdlib': '📚 Standard Library',
            'site-packages': '📦 Site Packages',
            'project': '🏗️ Project Files',
            'other': '📄 Other Files'
        }

        sections = []
        for module_type in ['project', 'stdlib', 'site-packages', 'other']:
            if module_type not in trees:
                continue

            tree = trees[module_type]

            # Project starts expanded, others start collapsed
            is_collapsed = module_type in {'stdlib', 'site-packages', 'other'}
            icon = '▶' if is_collapsed else '▼'
            content_style = ' style="display: none;"' if is_collapsed else ''

            file_word = "file" if tree.count == 1 else "files"
            sample_word = "sample" if tree.samples == 1 else "samples"
            section_html = f'''
<div class="type-section">
  <div class="type-header" onclick="toggleTypeSection(this)">
    <span class="type-icon">{icon}</span>
    <span class="type-title">{type_names[module_type]}</span>
    <span class="type-stats">({tree.count} {file_word}, {tree.samples:n} {sample_word})</span>
  </div>
  <div class="type-content"{content_style}>
'''

            # Render root folders
            root_folders = sorted(tree.children.items(),
                                key=lambda x: x[1].samples, reverse=True)

            for folder_name, folder_node in root_folders:
                section_html += self._render_folder(folder_node, folder_name, level=1)

            # Render root files (files not in any module)
            if tree.files:
                sorted_files = sorted(tree.files, key=lambda x: x.total_samples, reverse=True)
                section_html += '    <div class="files-list">\n'
                for stat in sorted_files:
                    section_html += self._render_file_item(stat, indent='      ')
                section_html += '    </div>\n'

            section_html += '  </div>\n</div>\n'
            sections.append(section_html)

        return '\n'.join(sections)