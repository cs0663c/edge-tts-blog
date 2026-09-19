# Edge-TTS 多人博客配音

基于 [rany2/edge-tts](https://github.com/rany2/edge-tts) 的网页工具：粘贴多人博客文本（`名字A：内容`），为每位说话人分配音色，逐段试听，最终一键导出合并好的 MP3。

## 功能

- 粘贴 `名字：内容` 格式文本，自动按说话人拆段
- 自动列出 edge-tts 全部可用音色（含中文普通话 / 粤语 / 台腔），为每个说话人指定音色
- 逐段试听，可调整语速、音调、段间静音
- 一键合成并下载合并后的 `narration.mp3`
- 记住每位说话人上次选的音色，下次自动沿用
- MP3 合并采用字节流拼接，无需 ffmpeg，镜像轻量

## 本地运行（开发）

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

浏览器打开 http://localhost:8000

## Docker 部署

### 本机单架构

```bash
docker build -t edge-tts-blog .
docker run -d -p 8000:8000 --restart unless-stopped edge-tts-blog
```

或用 Compose：

```bash
docker compose up -d --build
```

### 多架构（amd64 + arm64）

需要本机装有 Docker Buildx（Docker Desktop 默认自带）：

```bash
docker buildx create --use --name multiarch || true
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t <你的镜像名>/edge-tts-blog:latest \
  --push .
```

### 通过 GitHub Actions 自动发布

推一个 `v*` 标签（或手动触发 workflow_dispatch）即可自动构建 `linux/amd64` + `linux/arm64` 双架构镜像并推送到 GHCR：

```bash
git tag v0.1.0
git push origin v0.1.0
```

镜像地址：`ghcr.io/<你的GitHub用户名>/edge-tts-blog:latest`

拉取后在任意架构机器上运行：

```bash
docker run -d -p 8000:8000 --restart unless-stopped ghcr.io/<你的GitHub用户名>/edge-tts-blog:latest
```

> 首次推送到 GHCR 时，请到 GitHub → Packages → 该包 → Settings，把 visibility 改为 Public（或保持私有并配置 `docker login ghcr.io`）。

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
