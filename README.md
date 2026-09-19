# Edge-TTS 多人博客配音

基于 [rany2/edge-tts](https://github.com/rany2/edge-tts) 的网页工具：粘贴多人博客文本（`名字A：内容`），为每位说话人分配音色，逐段试听，最终一键导出合并好的 MP3。

默认对外端口 **2868**。

## 功能

- 粘贴 `名字：内容` 格式文本，自动按说话人拆段
- 自动列出 edge-tts 全部可用音色（含中文普通话 / 粤语 / 台腔），为每个说话人指定音色
- 逐段试听，可调整语速、音调、段间静音
- 一键合成并下载合并后的 `narration.mp3`
- 记住每位说话人上次选的音色，下次自动沿用
- MP3 合并采用字节流拼接，无需 ffmpeg，镜像轻量
- Docker 镜像同时支持 `linux/amd64` 与 `linux/arm64`

## 本地运行（开发）

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 2868 --reload
```

浏览器打开 http://localhost:2868

## Docker Compose 部署（推荐）

项目根目录已附带 `docker-compose.yml`，直接拉取 GHCR 上的预构建镜像，一条命令启动：

```bash
# 克隆仓库后进入目录
cd edge-tts-blog

# 后台启动（自动拉取 ghcr.io/cs0663c/edge-tts-blog:latest）
docker compose up -d
```

启动后访问 http://localhost:2868

### docker-compose.yml（直接拉 GHCR 镜像，无需本地构建）

```yaml
services:
  edge-tts-blog:
    image: ghcr.io/cs0663c/edge-tts-blog:latest   # GHCR 预构建镜像（amd64+arm64）
    container_name: edge-tts-blog
    ports:
      - "2868:8000"      # 宿主机 2868 → 容器内 8000
    restart: unless-stopped
```

常用操作：

```bash
docker compose pull            # 拉取最新镜像
docker compose up -d            # 启动
docker compose ps               # 查看运行状态
docker compose logs -f          # 跟踪日志
docker compose down             # 停止并移除容器
```

> 端口映射说明：`2868:8000` 左边是宿主机对外端口（你在浏览器访问的端口），右边是容器内 FastAPI 监听端口，保持 8000 即可。想换对外端口只改冒号左边，例如 `"18080:8000"`。

### 从本地源码构建（改代码后用）

如果想自己改代码并构建镜像，把 `image` 换成 `build: .`：

```yaml
services:
  edge-tts-blog:
    build: .
    image: edge-tts-blog:latest
    container_name: edge-tts-blog
    ports:
      - "2868:8000"
    restart: unless-stopped
```

然后：

```bash
docker compose up -d --build
```

## 直接用 Docker 命令部署

### 用 GHCR 镜像（无需本地构建，自动支持 amd64 / arm64）

```bash
docker pull ghcr.io/cs0663c/edge-tts-blog:latest
docker run -d \
  --name edge-tts-blog \
  -p 2868:8000 \
  --restart unless-stopped \
  ghcr.io/cs0663c/edge-tts-blog:latest
```

访问 http://服务器IP:2868

> 若镜像设为 Private，先执行 `docker login ghcr.io`（用户名填 GitHub 用户名，密码用 Personal Access Token）。

### 本地源码构建

```bash
docker build -t edge-tts-blog .
docker run -d -p 2868:8000 --restart unless-stopped edge-tts-blog
```

## 多架构镜像构建（amd64 + arm64）

### 方式一：GitHub Actions 自动构建（已配置）

仓库里已带 `.github/workflows/docker-publish.yml`。打一个 `v*` 标签即自动构建双架构镜像并推送到 GHCR：

```bash
git tag v0.1.0
git push origin v0.1.0
```

构建完成后镜像地址：`ghcr.io/cs0663c/edge-tts-blog:latest`

### 方式二：本地 buildx 手动构建

需要本机装有 Docker Buildx（Docker Desktop 默认自带）：

```bash
docker buildx create --use --name multiarch || true
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/cs0663c/edge-tts-blog:latest \
  --push .
```

## 文本格式

每行一段，写法不区分中英文冒号：

```
主持人林：欢迎来到本期播客。
嘉宾陈：好的，今天我们聊聊独立开发。
主持人林：工具链成熟了，一个人也能做出完整产品。
```

没有 `名字：` 前缀的行会自动接到上一段。

## 技术栈

- 后端：FastAPI + edge-tts
- 前端：原生 HTML/CSS/JS（单文件）
- 容器：python:3.12-slim（官方多架构 manifest，amd64 / arm64 通用）
- 默认对外端口：2868
