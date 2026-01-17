# -*- coding: utf-8 -*-
"""
WordPress XML 数据清洗工具
==========================
将 WordPress 导出的 XML 文件转换为按分类拆分的 Markdown 文件。

使用方式:
    python wordpress_cleaner.py <输入XML文件路径>

输出:
    在输入文件同目录下创建 "wordpress_cleaned" 文件夹。
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from html import unescape
from collections import defaultdict
from urllib.parse import unquote


# WordPress XML 命名空间
NAMESPACES = {
    'wp': 'http://wordpress.org/export/1.2/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
    'dc': 'http://purl.org/dc/elements/1.1/',
}

# 博主邮箱（用于过滤评论，请修改为你自己的邮箱）
AUTHOR_EMAIL = 'your_email@example.com'


def html_to_markdown(html_content: str) -> str:
    """将 HTML 内容转换为 Markdown"""
    if not html_content:
        return ""
    
    text = html_content
    
    # 处理 WordPress 区块注释
    text = re.sub(r'<!-- wp:[^>]+ -->', '', text)
    text = re.sub(r'<!-- /wp:[^>]+ -->', '', text)
    
    # 处理代码块
    text = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'\n```\n\1\n```\n', text, flags=re.DOTALL)
    text = re.sub(r'<code>(.*?)</code>', r'`\1`', text)
    
    # 处理标题
    text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1\n', text, flags=re.DOTALL)
    
    # 处理加粗和斜体
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text, flags=re.DOTALL)
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text, flags=re.DOTALL)
    text = re.sub(r'<i>(.*?)</i>', r'*\1*', text, flags=re.DOTALL)
    
    # 处理链接
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.DOTALL)
    
    # 处理图片
    text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*/?\s*>', r'![\2](\1)', text)
    text = re.sub(r'<img[^>]*src="([^"]*)"[^>]*/?\s*>', r'![image](\1)', text)
    
    # 处理列表
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', text, flags=re.DOTALL)
    text = re.sub(r'<ul[^>]*>', '', text)
    text = re.sub(r'</ul>', '\n', text)
    text = re.sub(r'<ol[^>]*>', '', text)
    text = re.sub(r'</ol>', '\n', text)
    
    # 处理段落和换行
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<hr\s*/?>', '\n---\n', text)
    
    # 处理引用块
    text = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'\n> \1\n', text, flags=re.DOTALL)
    
    # 清理剩余 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 处理 HTML 实体
    text = unescape(text)
    
    # 清理多余空行和空格
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()


def get_text(elem, tag, namespaces=None) -> str:
    """安全获取元素文本"""
    if namespaces:
        child = elem.find(tag, namespaces)
    else:
        child = elem.find(tag)
    return child.text.strip() if child is not None and child.text else ""


def parse_post(item) -> dict:
    """解析单篇文章"""
    post = {
        'id': get_text(item, 'wp:post_id', NAMESPACES),
        'title': get_text(item, 'title'),
        'link': get_text(item, 'link'),
        'date': get_text(item, 'wp:post_date', NAMESPACES),
        'status': get_text(item, 'wp:status', NAMESPACES),
        'type': get_text(item, 'wp:post_type', NAMESPACES),
        'content': '',
        'categories': [],
        'tags': [],
        'comments': [],
    }
    
    # 获取内容
    content_elem = item.find('content:encoded', NAMESPACES)
    if content_elem is not None and content_elem.text:
        post['content'] = html_to_markdown(content_elem.text)
    
    # 获取分类和标签
    for cat in item.findall('category'):
        domain = cat.get('domain', '')
        cat_name = cat.text
        if cat_name:
            if domain == 'category':
                post['categories'].append(cat_name)
            elif domain == 'post_tag':
                post['tags'].append(cat_name)
    
    # 获取评论（只保留博主自己的）
    for comment in item.findall('wp:comment', NAMESPACES):
        author_email = get_text(comment, 'wp:comment_author_email', NAMESPACES)
        if author_email == AUTHOR_EMAIL:
            comment_data = {
                'author': get_text(comment, 'wp:comment_author', NAMESPACES),
                'date': get_text(comment, 'wp:comment_date', NAMESPACES),
                'content': get_text(comment, 'wp:comment_content', NAMESPACES),
            }
            post['comments'].append(comment_data)
    
    return post


# 主要分类（用于合并）
MAIN_CATEGORIES = ['学习历程', '生活流水账', '所思所感', '未分类']


def get_main_category(categories: list) -> str:
    """获取主分类，如果没有主分类则归入其他"""
    for cat in categories:
        if cat in MAIN_CATEGORIES:
            return cat
    # 如果没有主分类，归入"其他"
    return '其他' if categories else '未分类'


def generate_post_markdown(post: dict) -> str:
    """生成单篇文章的 Markdown"""
    lines = []
    
    # 标题
    title = post['title'] or '无标题'
    lines.append(f"## {title}\n")
    
    # 元数据
    if post['date']:
        lines.append(f"**发布时间**: {post['date']}")
    if post['status'] != 'publish':
        lines.append(f"**状态**: {post['status']}")
    if post['categories']:
        lines.append(f"**分类**: {', '.join(post['categories'])}")
    if post['link']:
        lines.append(f"**链接**: {post['link']}")
    
    lines.append("")
    
    # 内容
    if post['content']:
        lines.append(post['content'])
    else:
        lines.append("*（无内容）*")
    
    # 评论
    if post['comments']:
        lines.append("\n### 我的评论\n")
        for c in post['comments']:
            lines.append(f"**{c['author']}** ({c['date']}):")
            lines.append(f"> {c['content']}\n")
    
    lines.append("\n---\n")
    
    return '\n'.join(lines)


def main():
    print("=" * 60)
    print("  WordPress XML 数据清洗工具 v1.0")
    print("  将 WordPress XML 转换为 Markdown")
    print("=" * 60)
    print()
    
    # 获取输入文件
    if len(sys.argv) < 2:
        current_dir = Path.cwd()
        xml_files = list(current_dir.glob("*.xml"))
        if xml_files:
            input_path = xml_files[0]
            print(f"📌 自动检测到 XML 文件: {input_path.name}")
        else:
            print("用法: python wordpress_cleaner.py <输入XML文件路径>")
            sys.exit(1)
    else:
        input_path = Path(sys.argv[1])
    
    if not input_path.exists():
        print(f"❌ 错误: 文件不存在: {input_path}")
        sys.exit(1)
    
    output_dir = input_path.parent / "wordpress_cleaned"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📖 正在读取文件: {input_path.name}")
    
    # 读取并清理 XML 内容（处理开头空行问题）
    with open(input_path, 'r', encoding='utf-8') as f:
        xml_content = f.read().lstrip()
    
    # 解析 XML
    root = ET.fromstring(xml_content)
    channel = root.find('channel')
    
    if channel is None:
        print("❌ 错误: 无效的 WordPress XML 格式")
        sys.exit(1)
    
    # 获取站点信息
    site_title = get_text(channel, 'title')
    print(f"   站点: {site_title}")
    
    # 解析所有文章
    posts_by_category = defaultdict(list)
    total_posts = 0
    total_comments = 0
    
    for item in channel.findall('item'):
        post = parse_post(item)
        
        # 只处理文章类型
        if post['type'] != 'post':
            continue
        
        total_posts += 1
        total_comments += len(post['comments'])
        
        # 按主分类分组（合并细分类到主分类）
        main_cat = get_main_category(post['categories'])
        posts_by_category[main_cat].append(post)
    
    print(f"✅ 共解析到 {total_posts} 篇文章, {total_comments} 条自己的评论")
    print(f"📊 按分类分组: {len(posts_by_category)} 个分类")
    
    # 生成分类文件
    print(f"\n📁 输出目录: {output_dir}")
    print("📝 正在生成分类文件...")
    
    for category, posts in sorted(posts_by_category.items()):
        # 按日期排序（最新在前）
        posts.sort(key=lambda x: x['date'] or '', reverse=True)
        
        # 生成 Markdown
        lines = [
            f"# {site_title} - {category}\n",
            f"> 共 {len(posts)} 篇文章\n",
            "---\n"
        ]
        
        for post in posts:
            lines.append(generate_post_markdown(post))
        
        content = '\n'.join(lines)
        
        # 文件名安全处理
        safe_category = re.sub(r'[<>:"/\\|?*]', '_', category)
        output_file = output_dir / f"{safe_category}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        file_size_kb = len(content) / 1024
        print(f"   ✓ {category}: {len(posts):3d} 篇, {file_size_kb:6.1f} KB")
    
    # 生成索引
    index_lines = [
        f"# {site_title} - 文章索引\n",
        f"> 共 {total_posts} 篇文章，{len(posts_by_category)} 个分类\n",
        "---\n",
        "## 分类列表\n",
        "| 分类 | 文章数 | 文件 |",
        "|------|--------|------|"
    ]
    
    for category, posts in sorted(posts_by_category.items(), key=lambda x: -len(x[1])):
        safe_category = re.sub(r'[<>:"/\\|?*]', '_', category)
        filename = f"{safe_category}.md"
        index_lines.append(f"| {category} | {len(posts)} | [{filename}](./{filename}) |")
    
    index_file = output_dir / "README.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(index_lines))
    
    print(f"   ✓ 索引文件: README.md")
    
    print()
    print("=" * 60)
    print("✅ 转换完成!")
    print(f"   输出目录: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
