def _extract_url(self, response):
        """从响应中提取PDF下载链接"""
        soup = BeautifulSoup(response.content, 'html.parser')
        try:
            # 尝试多种方式提取PDF链接
            pdf_element = soup.find(id='pdf')
            if pdf_element:
                content_url = pdf_element.get('src')
            else:
                # 尝试其他可能的选择器
                pdf_element = soup.find('iframe')
                if pdf_element:
                    content_url = pdf_element.get('src')
                else:
                    # 查找直接的PDF链接
                    pdf_links = soup.find_all('a', href=lambda x: x and '.pdf' in x)
                    if pdf_links:
                        content_url = pdf_links[0].get('href')
                    else:
                        raise AttributeError("未找到PDF链接")

            if content_url:
                content_url = content_url.replace('#navpanes=0&view=FitH', '').replace('//', '/')
                if not content_url.endswith('.pdf') and 'pdf' not in content_url.lower():
                    raise AttributeError("找到的链接不是PDF文件")
        except AttributeError:
            logger.error(f"未找到论文 {self.doi}")
            return None

        current_mirror = self.url.rstrip('/')
        if content_url.startswith('/'):
            return current_mirror + content_url
        elif content_url.startswith('http'):
            return content_url
        else:
            return 'https:/' + content_url