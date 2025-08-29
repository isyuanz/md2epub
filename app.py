#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web服务：Markdown to EPUB 转换器
"""

import os
import io
import uuid
import shutil
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from md2ebook import MarkdownEbookConverter

# 创建Flask应用
app = Flask(__name__)
app.secret_key = 'md2epub_secret_key_change_in_production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 配置上传目录
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'md', 'markdown', 'txt'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER


def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def cleanup_old_files():
    """清理超过1小时的临时文件"""
    import time
    current_time = time.time()
    
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                filepath = os.path.join(folder, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    # 删除超过1小时的文件
                    if current_time - file_time > 3600:
                        try:
                            os.remove(filepath)
                        except:
                            pass


@app.route('/')
def index():
    """主页"""
    cleanup_old_files()
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传Markdown文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件被上传'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
            # 生成唯一文件名
            unique_id = str(uuid.uuid4())
            filename = secure_filename(f"{unique_id}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # 保存文件
            file.save(filepath)
            
            # 读取文件内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取文件名作为默认标题
            title = os.path.splitext(file.filename)[0]
            
            return jsonify({
                'success': True,
                'content': content,
                'title': title,
                'file_id': unique_id
            })
        else:
            return jsonify({'error': '不支持的文件格式，请上传 .md, .markdown 或 .txt 文件'}), 400
            
    except RequestEntityTooLarge:
        return jsonify({'error': '文件太大，请上传小于16MB的文件'}), 413
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500


@app.route('/api/upload_cover', methods=['POST'])
def upload_cover():
    """上传封面图片"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有文件被上传'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            # 生成唯一文件名
            unique_id = str(uuid.uuid4())
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{unique_id}_cover.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # 保存文件
            file.save(filepath)
            
            return jsonify({
                'success': True,
                'cover_id': unique_id,
                'filename': file.filename
            })
        else:
            return jsonify({'error': '不支持的图片格式，请上传 PNG, JPG 或 JPEG 文件'}), 400
            
    except RequestEntityTooLarge:
        return jsonify({'error': '图片文件太大，请上传小于16MB的文件'}), 413
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500


@app.route('/api/convert', methods=['POST'])
def convert_to_epub():
    """转换Markdown为EPUB"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        if not data.get('title') or not data.get('author') or not data.get('content'):
            return jsonify({'error': '请填写完整的书籍信息和内容'}), 400
        
        title = data['title'].strip()
        author = data['author'].strip()
        content = data['content'].strip()
        cover_id = data.get('cover_id')
        
        # 生成唯一ID用于文件名
        unique_id = str(uuid.uuid4())
        
        # 创建临时Markdown文件
        md_filename = f"{unique_id}_temp.md"
        md_filepath = os.path.join(app.config['UPLOAD_FOLDER'], md_filename)
        
        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 创建转换器实例
        converter = MarkdownEbookConverter()
        
        # 处理封面图片（如果有）
        cover_path = None
        if cover_id:
            # 查找对应的封面文件
            for ext in ['png', 'jpg', 'jpeg', 'gif']:
                potential_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{cover_id}_cover.{ext}")
                if os.path.exists(potential_path):
                    cover_path = potential_path
                    break
        
        # 设置输出文件路径
        epub_filename = f"{unique_id}_{secure_filename(title)}.epub"
        epub_filepath = os.path.join(app.config['OUTPUT_FOLDER'], epub_filename)
        
        # 解析Markdown
        html_content = converter.parse_markdown_content(content)
        
        # 提取标题
        headings = converter.extract_headings(html_content)
        
        # 分割章节
        chapters = converter.split_content_by_chapters(html_content, headings)
        
        # 创建EPUB（修改create_epub方法以支持封面）
        converter.create_epub_with_cover(chapters, headings, title, author, epub_filepath, cover_path)
        
        return jsonify({
            'success': True,
            'message': 'EPUB文件生成成功！',
            'download_id': unique_id,
            'filename': epub_filename
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'转换失败: {str(e)}'}), 500


@app.route('/api/download/<download_id>')
def download_file(download_id):
    """下载生成的EPUB文件"""
    try:
        # 查找文件
        output_dir = app.config['OUTPUT_FOLDER']
        epub_file = None
        
        for filename in os.listdir(output_dir):
            if filename.startswith(download_id) and filename.endswith('.epub'):
                epub_file = os.path.join(output_dir, filename)
                break
        
        if not epub_file or not os.path.exists(epub_file):
            return jsonify({'error': '文件不存在或已过期'}), 404
        
        # 提取原始文件名
        display_name = os.path.basename(epub_file)
        if '_' in display_name:
            display_name = '_'.join(display_name.split('_')[1:])
        
        return send_file(
            epub_file,
            as_attachment=True,
            download_name=display_name,
            mimetype='application/epub+zip'
        )
        
    except Exception as e:
        return jsonify({'error': f'下载失败: {str(e)}'}), 500




@app.errorhandler(413)
def too_large(e):
    """处理文件太大错误"""
    return jsonify({'error': '文件太大，请上传小于16MB的文件'}), 413


@app.errorhandler(500)
def internal_error(e):
    """处理内部错误"""
    return jsonify({'error': '服务器内部错误，请稍后重试'}), 500


# 扩展原有的MarkdownEbookConverter类
class EnhancedMarkdownEbookConverter(MarkdownEbookConverter):
    """增强的Markdown转换器，支持封面图片"""
    
    def parse_markdown_content(self, content):
        """直接解析Markdown内容字符串"""
        import markdown
        
        md = markdown.Markdown(extensions=[
            'extra',
            'toc', 
            'codehilite',
            'tables'
        ])
        html = md.convert(content)
        return html
    
    def create_epub_with_cover(self, chapters, headings, title, author, output_file, cover_path=None):
        """创建带封面的EPUB文件"""
        from ebooklib import epub
        import base64
        
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
        code {
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }
        pre {
            background-color: #f8f8f8;
            padding: 1em;
            border-radius: 5px;
            overflow-x: auto;
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
        toc_entries = []
        
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
            
            # 添加到目录
            toc_entries.append(epub.Link(chapter_file, chapter['title'], chapter_id))
        
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


# 替换原有的转换器
MarkdownEbookConverter = EnhancedMarkdownEbookConverter


if __name__ == '__main__':
    print("🚀 启动 Markdown to EPUB Web 服务...")
    print("📚 访问地址: http://localhost:5000")
    print("⚡ 按 Ctrl+C 停止服务")
    
    # 开发模式运行
    app.run(host='0.0.0.0', port=5000, debug=True)