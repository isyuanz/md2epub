#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to EPUB Converter Module
将Markdown文档转换为EPUB格式的电子书
"""

import os
import re
import markdown
from bs4 import BeautifulSoup
from ebooklib import epub


class MarkdownEbookConverter:
    """Markdown转EPUB转换器"""
    
    def __init__(self):
        """初始化转换器"""
        pass
    
    def parse_markdown_content(self, content):
        """解析Markdown内容为HTML
        
        Args:
            content (str): Markdown内容字符串
            
        Returns:
            str: 转换后的HTML内容
        """
        md = markdown.Markdown(extensions=[
            'extra',
            'toc', 
            'codehilite',
            'tables',
            'fenced_code'
        ], extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': True,
                'guess_lang': True,
                'linenums': False
            }
        })
        html = md.convert(content)
        
        # 处理代码块，添加语言标签
        html = self._process_code_blocks(html)
        
        return html
    
    def _process_code_blocks(self, html):
        """处理代码块，添加语言标签和改进样式
        
        Args:
            html (str): HTML内容
            
        Returns:
            str: 处理后的HTML内容
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # 处理所有代码块
        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                # 获取语言信息
                lang = None
                classes = code.get('class', [])
                
                # 从class中提取语言信息
                for cls in classes:
                    if cls.startswith('language-'):
                        lang = cls.replace('language-', '')
                        break
                    elif cls.startswith('highlight-'):
                        lang = cls.replace('highlight-', '')
                        break
                
                # 如果没有指定语言，尝试从内容推断
                if not lang:
                    code_text = code.get_text().strip().lower()
                    lang = self._guess_language(code_text)
                
                # 添加语言标签
                if lang:
                    lang_span = soup.new_tag('span', class_='code-lang')
                    lang_span.string = lang.upper()
                    pre.insert(0, lang_span)
                
                # 确保pre标签有正确的class
                if 'highlight' not in pre.get('class', []):
                    pre['class'] = pre.get('class', []) + ['highlight']
        
        return str(soup)
    
    def _guess_language(self, code_text):
        """根据代码内容推断编程语言
        
        Args:
            code_text (str): 代码文本
            
        Returns:
            str: 推断的语言名称，如果无法推断则返回'text'
        """
        # SQL关键字检测
        sql_keywords = ['select', 'insert', 'update', 'delete', 'create', 'drop', 'alter', 'from', 'where', 'join']
        if any(keyword in code_text for keyword in sql_keywords):
            return 'sql'
        
        # Python关键字检测
        python_keywords = ['def ', 'import ', 'from ', 'class ', 'if __name__', 'print(']
        if any(keyword in code_text for keyword in python_keywords):
            return 'python'
        
        # JavaScript关键字检测
        js_keywords = ['function', 'var ', 'let ', 'const ', 'console.log', '=>']
        if any(keyword in code_text for keyword in js_keywords):
            return 'javascript'
        
        # Java关键字检测
        java_keywords = ['public class', 'public static', 'system.out.println']
        if any(keyword in code_text for keyword in java_keywords):
            return 'java'
        
        # HTML标签检测
        if '<' in code_text and '>' in code_text and any(tag in code_text for tag in ['<html', '<div', '<p>', '<span']):
            return 'html'
        
        # CSS检测
        if '{' in code_text and '}' in code_text and ':' in code_text:
            return 'css'
        
        # Shell/Bash检测
        bash_keywords = ['#!/bin/bash', 'echo ', 'cd ', 'ls ', 'chmod ', 'sudo ']
        if any(keyword in code_text for keyword in bash_keywords):
            return 'bash'
        
        # 如果无法推断，返回通用类型
        return 'text'
    
    def extract_headings(self, html_content):
        """提取HTML中的标题结构
        
        Args:
            html_content (str): HTML内容
            
        Returns:
            list: 标题列表，每个元素包含level, title, id等信息
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        headings = []
        
        for i, heading in enumerate(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])):
            level = int(heading.name[1])  # 提取数字部分
            title = heading.get_text().strip()
            
            # 生成ID
            heading_id = f"heading_{i}"
            heading['id'] = heading_id
            
            headings.append({
                'level': level,
                'title': title,
                'id': heading_id,
                'element': heading
            })
        
        return headings
    
    def split_content_by_chapters(self, html_content, headings):
        """根据标题将内容分割为章节
        
        Args:
            html_content (str): HTML内容
            headings (list): 标题列表
            
        Returns:
            list: 章节列表，每个章节包含title和content
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        chapters = []
        
        if not headings:
            # 如果没有标题，整个内容作为一章
            chapters.append({
                'title': '正文',
                'content': str(soup)
            })
            return chapters
        
        # 找到所有一级标题作为章节分界点
        h1_headings = [h for h in headings if h['level'] == 1]
        
        if not h1_headings:
            # 如果没有一级标题，使用二级标题
            h1_headings = [h for h in headings if h['level'] == 2]
        
        if not h1_headings:
            # 如果没有二级标题，整个内容作为一章
            chapters.append({
                'title': '正文',
                'content': str(soup)
            })
            return chapters
        
        # 按章节分割内容
        for i, heading in enumerate(h1_headings):
            chapter_title = heading['title']
            
            # 找到当前章节的开始和结束位置
            current_element = heading['element']
            chapter_content = []
            
            # 收集从当前标题到下一个同级标题之间的所有内容
            next_sibling = current_element
            while next_sibling:
                next_sibling = next_sibling.find_next_sibling()
                
                if next_sibling and next_sibling.name in ['h1', 'h2'] and \
                   (next_sibling.name == 'h1' or (heading['level'] == 2 and next_sibling.name == 'h2')):
                    # 遇到下一个同级或更高级标题，停止
                    break
                elif next_sibling:
                    chapter_content.append(str(next_sibling))
            
            # 包含当前标题
            full_content = str(current_element) + ''.join(chapter_content)
            
            chapters.append({
                'title': chapter_title,
                'content': full_content
            })
        
        return chapters
    
    def create_detailed_toc(self, headings, chapters):
        """创建详细的目录结构
        
        Args:
            headings (list): 标题列表
            chapters (list): 章节列表
            
        Returns:
            list: EPUB目录结构
        """
        toc_entries = []
        
        for i, chapter in enumerate(chapters):
            chapter_file = f"chapter_{i}.xhtml"
            toc_entries.append(epub.Link(chapter_file, chapter['title'], f"chapter_{i}"))
        
        return toc_entries
    
    def create_epub(self, chapters, headings, title, author, output_file):
        """创建EPUB文件
        
        Args:
            chapters (list): 章节列表
            headings (list): 标题列表
            title (str): 书籍标题
            author (str): 作者
            output_file (str): 输出文件路径
        """
        book = epub.EpubBook()
        
        # 设置书籍元数据
        book.set_identifier('md2epub')
        book.set_title(title)
        book.set_language('zh-CN')
        book.add_author(author)
        
        # CSS样式
        style = '''
        body { 
            font-family: "Microsoft YaHei", "SimSun", serif; 
            line-height: 1.6;
            margin: 2em;
        }
        h1, h2, h3, h4, h5, h6 { 
            color: #333; 
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }
        h1 { 
            font-size: 1.8em; 
            border-bottom: 2px solid #333;
            padding-bottom: 0.3em;
        }
        h2 { 
            font-size: 1.5em;
            color: #666;
        }
        h3 { 
            font-size: 1.3em;
        }
        p { 
            margin-bottom: 1em;
            text-align: justify;
        }
        ul, ol {
            margin-left: 2em;
        }
        li {
            margin-bottom: 0.5em;
        }
        strong {
            font-weight: bold;
            color: #d73502;
        }
        /* 行内代码样式 */
        code {
            background-color: #f1f3f4;
            color: #c7254e;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 0.9em;
            border: 1px solid #e1e4e8;
        }
        /* 代码块样式 */
        pre {
            background-color: #f8f9fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 16px;
            margin: 16px 0;
            overflow-x: auto;
            line-height: 1.45;
            position: relative;
        }
        pre code {
            background-color: transparent;
            color: #24292e;
            padding: 0;
            border: none;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 0.85em;
            white-space: pre;
            word-wrap: normal;
        }
        /* 代码块语言标签 */
        .code-lang {
            position: absolute;
            top: 8px;
            right: 12px;
            font-size: 0.75em;
            color: #586069;
            background-color: #ffffff;
            padding: 2px 6px;
            border-radius: 3px;
            border: 1px solid #e1e4e8;
        }
        /* 语法高亮 - 关键字 */
        .highlight .k, .highlight .kd, .highlight .kn, .highlight .kr, .highlight .kt { 
            color: #d73a49; 
            font-weight: bold; 
        }
        /* 语法高亮 - 字符串 */
        .highlight .s, .highlight .s1, .highlight .s2, .highlight .sb, .highlight .sc { 
            color: #032f62; 
        }
        /* 语法高亮 - 注释 */
        .highlight .c, .highlight .c1, .highlight .cm { 
            color: #6a737d; 
            font-style: italic; 
        }
        /* 语法高亮 - 数字 */
        .highlight .m, .highlight .mi, .highlight .mf, .highlight .mh, .highlight .mo { 
            color: #005cc5; 
        }
        /* 语法高亮 - 函数名 */
        .highlight .nf { 
            color: #6f42c1; 
            font-weight: bold; 
        }
        /* 语法高亮 - 变量 */
        .highlight .n, .highlight .na, .highlight .nb, .highlight .nc, .highlight .nd, .highlight .ne, .highlight .ni, .highlight .nl, .highlight .nn, .highlight .nt, .highlight .nv, .highlight .nx { 
            color: #24292e; 
        }
        /* 语法高亮 - 操作符 */
        .highlight .o { 
            color: #d73a49; 
        }
        blockquote {
            border-left: 4px solid #ddd;
            margin-left: 0;
            padding-left: 1em;
            color: #666;
        }
        '''
        
        nav_css = epub.EpubItem(uid="nav_css",
                               file_name="style/nav.css",
                               media_type="text/css",
                               content=style)
        book.add_item(nav_css)
        
        # 创建章节
        epub_chapters = []
        
        for i, chapter in enumerate(chapters):
            chapter_id = f"chapter_{i}"
            chapter_file = f"chapter_{i}.xhtml"
            
            # 包装HTML内容
            html_content = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{chapter['title']}</title>
    <link rel="stylesheet" type="text/css" href="style/nav.css"/>
</head>
<body>
{chapter['content']}
</body>
</html>'''
            
            c = epub.EpubHtml(title=chapter['title'],
                             file_name=chapter_file,
                             lang='zh-CN')
            c.content = html_content
            
            book.add_item(c)
            epub_chapters.append(c)
        
        # 生成目录结构
        detailed_toc = self.create_detailed_toc(headings, chapters)
        book.toc = detailed_toc
        
        # 添加导航文件
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # 设置书脊
        book.spine = ['nav'] + epub_chapters
        
        # 写入EPUB文件
        epub.write_epub(output_file, book, {})
    
    def create_epub_with_cover(self, chapters, headings, title, author, output_file, cover_path=None):
        """创建带封面的EPUB文件
        
        Args:
            chapters (list): 章节列表
            headings (list): 标题列表
            title (str): 书籍标题
            author (str): 作者
            output_file (str): 输出文件路径
            cover_path (str, optional): 封面图片路径
        """
        book = epub.EpubBook()
        
        # 设置书籍元数据
        book.set_identifier('md2epub-web')
        book.set_title(title)
        book.set_language('zh-CN')
        book.add_author(author)
        
        # 添加封面图片
        if cover_path and os.path.exists(cover_path):
            with open(cover_path, 'rb') as f:
                cover_image = f.read()
            
            # 确定图片类型
            ext = cover_path.split('.')[-1].lower()
            media_type = f"image/{ext}" if ext in ['png', 'gif'] else "image/jpeg"
            
            book.set_cover("cover.jpg", cover_image)
        
        # CSS样式
        style = '''
        body { 
            font-family: "Microsoft YaHei", "SimSun", serif; 
            line-height: 1.6;
            margin: 2em;
        }
        h1, h2, h3, h4, h5, h6 { 
            color: #333; 
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }
        h1 { 
            font-size: 1.8em; 
            border-bottom: 2px solid #333;
            padding-bottom: 0.3em;
        }
        h2 { 
            font-size: 1.5em;
            color: #666;
        }
        h3 { 
            font-size: 1.3em;
        }
        p { 
            margin-bottom: 1em;
            text-align: justify;
        }
        ul, ol {
            margin-left: 2em;
        }
        li {
            margin-bottom: 0.5em;
        }
        strong {
            font-weight: bold;
            color: #d73502;
        }
        /* 行内代码样式 */
        code {
            background-color: #f1f3f4;
            color: #c7254e;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 0.9em;
            border: 1px solid #e1e4e8;
        }
        /* 代码块样式 */
        pre {
            background-color: #f8f9fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 16px;
            margin: 16px 0;
            overflow-x: auto;
            line-height: 1.45;
            position: relative;
        }
        pre code {
            background-color: transparent;
            color: #24292e;
            padding: 0;
            border: none;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 0.85em;
            white-space: pre;
            word-wrap: normal;
        }
        /* 代码块语言标签 */
        .code-lang {
            position: absolute;
            top: 8px;
            right: 12px;
            font-size: 0.75em;
            color: #586069;
            background-color: #ffffff;
            padding: 2px 6px;
            border-radius: 3px;
            border: 1px solid #e1e4e8;
        }
        /* 语法高亮 - 关键字 */
        .highlight .k, .highlight .kd, .highlight .kn, .highlight .kr, .highlight .kt { 
            color: #d73a49; 
            font-weight: bold; 
        }
        /* 语法高亮 - 字符串 */
        .highlight .s, .highlight .s1, .highlight .s2, .highlight .sb, .highlight .sc { 
            color: #032f62; 
        }
        /* 语法高亮 - 注释 */
        .highlight .c, .highlight .c1, .highlight .cm { 
            color: #6a737d; 
            font-style: italic; 
        }
        /* 语法高亮 - 数字 */
        .highlight .m, .highlight .mi, .highlight .mf, .highlight .mh, .highlight .mo { 
            color: #005cc5; 
        }
        /* 语法高亮 - 函数名 */
        .highlight .nf { 
            color: #6f42c1; 
            font-weight: bold; 
        }
        /* 语法高亮 - 变量 */
        .highlight .n, .highlight .na, .highlight .nb, .highlight .nc, .highlight .nd, .highlight .ne, .highlight .ni, .highlight .nl, .highlight .nn, .highlight .nt, .highlight .nv, .highlight .nx { 
            color: #24292e; 
        }
        /* 语法高亮 - 操作符 */
        .highlight .o { 
            color: #d73a49; 
        }
        blockquote {
            border-left: 4px solid #ddd;
            margin-left: 0;
            padding-left: 1em;
            color: #666;
        }
        '''
        
        nav_css = epub.EpubItem(uid="nav_css",
                               file_name="style/nav.css",
                               media_type="text/css",
                               content=style)
        book.add_item(nav_css)
        
        # 创建章节
        epub_chapters = []
        
        for i, chapter in enumerate(chapters):
            chapter_id = f"chapter_{i}"
            chapter_file = f"chapter_{i}.xhtml"
            
            # 包装HTML内容
            html_content = f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>{chapter['title']}</title>
    <link rel="stylesheet" type="text/css" href="style/nav.css"/>
</head>
<body>
{chapter['content']}
</body>
</html>'''
            
            c = epub.EpubHtml(title=chapter['title'],
                             file_name=chapter_file,
                             lang='zh-CN')
            c.content = html_content
            
            book.add_item(c)
            epub_chapters.append(c)
        
        # 生成详细目录结构
        detailed_toc = self.create_detailed_toc(headings, chapters)
        book.toc = detailed_toc
        
        # 添加导航文件
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # 设置书脊
        book.spine = ['nav'] + epub_chapters
        
        # 写入EPUB文件
        epub.write_epub(output_file, book, {})


if __name__ == "__main__":
    # 测试代码
    converter = MarkdownEbookConverter()
    
    test_markdown = """
# 第一章 开始
这是第一章的内容。

## 1.1 小节
这是一个小节的内容。

# 第二章 继续
这是第二章的内容。

## 2.1 另一个小节
更多内容在这里。
"""
    
    html = converter.parse_markdown_content(test_markdown)
    headings = converter.extract_headings(html)
    chapters = converter.split_content_by_chapters(html, headings)
    
    print(f"找到 {len(headings)} 个标题")
    print(f"分割为 {len(chapters)} 个章节")
    
    for i, chapter in enumerate(chapters):
        print(f"章节 {i+1}: {chapter['title']}")