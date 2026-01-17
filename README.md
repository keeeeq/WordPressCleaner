# WordPress 数据清洗工具

将 WordPress 导出的 XML 文件转换为按分类拆分的 Markdown 文件，便于导入 NotebookLM 等工具进行分析。

## 功能特性

- ✅ 解析 WordPress WXR (eXtended RSS) 格式
- ✅ 自动合并细分类到主分类
- ✅ 只保留博主自己的评论（过滤垃圾评论）
- ✅ 支持草稿和已发布文章
- ✅ HTML 转 Markdown（保留格式）

## 快速开始

### 方法一：双击运行（推荐）

1. 双击 `一键启动.bat`
2. 将 XML 文件拖放到窗口中
3. 等待处理完成

### 方法二：命令行运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python wordpress_cleaner.py "你的WordPress导出.xml"
```

## 输出结构

```
XML所在目录/
└── wordpress_cleaned/
    ├── README.md       # 索引文件
    ├── 学习历程.md
    ├── 生活流水账.md
    ├── 所思所感.md
    ├── 未分类.md
    └── 其他.md
```

## 如何导出 WordPress 数据

1. 登录 WordPress 后台
2. 进入 **工具 → 导出**
3. 选择"所有内容"
4. 点击"下载导出的文件"

## 自定义配置

修改 `wordpress_cleaner.py` 中的以下变量：

```python
# 博主邮箱（用于过滤评论）
AUTHOR_EMAIL = '你的邮箱@example.com'

# 主要分类（其他分类会合并到"其他"）
MAIN_CATEGORIES = ['学习历程', '生活流水账', '所思所感', '未分类']
```

## 依赖

- Python 3.8+
- 无第三方依赖（仅使用标准库）

## 文件说明

| 文件 | 说明 |
|------|------|
| `wordpress_cleaner.py` | 主程序 |
| `一键启动.bat` | Windows 一键启动脚本 |
| `README.md` | 本说明文档 |
