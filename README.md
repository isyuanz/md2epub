# Markdown to EPUB Web 转换器

一个基于 Flask 的 Web 服务，可以将 Markdown 文档转换为精美的 EPUB 电子书，支持封面图片上传和实时预览。

## 🌟 功能特点

- ✅ **Web 界面操作** - 直观的网页界面，无需命令行
- ✅ **文件上传支持** - 支持拖拽上传 Markdown 文件和封面图片
- ✅ **实时预览** - 在线预览 Markdown 转换效果
- ✅ **封面图片** - 支持自定义 EPUB 封面图片
- ✅ **自动章节分割** - 根据 H1 标题自动分割章节
- ✅ **响应式设计** - 适配 PC 和移动设备
- ✅ **RESTful API** - 提供完整的 API 接口

## 📦 安装与运行

### 方法一：使用启动脚本（推荐）

**Windows:**

```bash
# 双击运行 start.bat
start.bat
```

**Linux/Mac:**

```bash
# 给脚本执行权限并运行
chmod +x start.sh
./start.sh
```

### 方法二：手动安装

1. **安装依赖**

```bash
pip install -r requirements-web.txt
```

2. **启动服务**

```bash
python run.py
# 或
python app.py
```

3. **访问服务**

```
http://localhost:5000
```

## 🎯 使用方法

### Web 界面使用

1. 打开浏览器访问 `http://localhost:5000`
2. 填写书籍标题和作者信息
3. 可选：上传封面图片（推荐 600x800 尺寸）
4. 输入或上传 Markdown 内容
5. 点击"预览"查看转换效果
6. 点击"生成 EPUB"下载电子书

### API 接口使用

**上传 Markdown 文件:**

```bash
curl -X POST -F "file=@sample.md" http://localhost:5000/api/upload
```

**上传封面图片:**

```bash
curl -X POST -F "file=@cover.jpg" http://localhost:5000/api/upload_cover
```

**转换为 EPUB:**

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"title":"我的书","author":"作者","content":"# 第一章\n内容..."}' \
  http://localhost:5000/api/convert
```

**预览内容:**

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"content":"# 标题\n内容"}' \
  http://localhost:5000/api/preview
```

## 📁 项目结构

```
md2mobi/
├── app.py                 # Flask主应用
├── run.py                 # 启动脚本
├── md2ebook.py           # 原始转换器模块
├── requirements-web.txt   # Web版本依赖
├── start.bat             # Windows启动脚本
├── start.sh              # Linux/Mac启动脚本
├── templates/
│   └── index.html        # 主页模板
├── static/
│   └── style.css         # 样式文件
├── uploads/              # 上传文件临时目录
└── output/               # 生成文件输出目录
```

## 🔧 配置选项

### 环境变量

- `HOST`: 绑定主机地址（默认：0.0.0.0）
- `PORT`: 端口号（默认：5000）
- `DEBUG`: 调试模式（默认：True）

### 应用配置

- `MAX_CONTENT_LENGTH`: 最大文件上传大小（16MB）
- 支持的文件格式：
  - Markdown: `.md`, `.markdown`, `.txt`
  - 图片: `.png`, `.jpg`, `.jpeg`, `.gif`

## 🚀 部署到生产环境

### 使用 Gunicorn 部署

1. **安装 Gunicorn**

```bash
pip install gunicorn
```

2. **启动服务**

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 使用 Docker 部署

1. **创建 Dockerfile**

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements-web.txt .
RUN pip install -r requirements-web.txt

COPY . .
EXPOSE 5000

CMD ["python", "run.py"]
```

2. **构建并运行**

```bash
docker build -t md2epub-web .
docker run -p 5000:5000 md2epub-web
```

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📝 API 文档

### 文件上传接口

**POST** `/api/upload`

- 上传 Markdown 文件
- 表单数据：`file`（文件）
- 返回：`{success, content, title, file_id}`

**POST** `/api/upload_cover`

- 上传封面图片
- 表单数据：`file`（图片文件）
- 返回：`{success, cover_id, filename}`

### 转换接口

**POST** `/api/convert`

- 转换 Markdown 为 EPUB
- JSON 数据：`{title, author, content, cover_id?}`
- 返回：`{success, message, download_id, filename}`

**GET** `/api/download/<download_id>`

- 下载生成的 EPUB 文件
- 返回：EPUB 文件下载

### 预览接口

**POST** `/api/preview`

- 预览 Markdown 内容
- JSON 数据：`{content}`
- 返回：`{success, html}`

## 🛠️ 开发说明

### 本地开发

1. 克隆项目并安装依赖
2. 设置 `DEBUG=True` 启用调试模式
3. 修改代码后自动重载

### 添加新功能

- 在 `app.py` 中添加新的路由和 API
- 在 `templates/index.html` 中添加前端界面
- 在 `static/style.css` 中添加样式

## 🔒 安全注意事项

- 文件上传大小限制（16MB）
- 自动清理超过 1 小时的临时文件
- 使用安全的文件名处理
- 生产环境请更改 `secret_key`

## 🐛 故障排除

**常见问题:**

1. **端口被占用**

   ```bash
   # 更改端口
   export PORT=8000
   python run.py
   ```

2. **依赖安装失败**

   ```bash
   # 升级pip
   pip install --upgrade pip
   pip install -r requirements-web.txt
   ```

3. **文件上传失败**
   - 检查文件大小是否超过 16MB
   - 确认文件格式是否支持

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
