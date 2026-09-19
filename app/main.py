"""FastAPI 入口：文本解析 / 音色列表 / 单段试听 / 整段合成导出。"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .parser import parse_blog_text
from .tts import DEFAULT_VOICES, list_voices, merge_mp3, synthesize

app = FastAPI(title="Edge-TTS 多人博客配音", version="1.0.0")

STATIC_DIR = Path(__file__).parent / "static"


# ---------- 请求体 ----------
class ParseRequest(BaseModel):
    text: str


class TTSRequest(BaseModel):
    text: str
    voice: str
    rate: str = "+0%"
    pitch: str = "+0Hz"


class NarrationSegment(BaseModel):
    speaker: str
    text: str
    voice: str
    rate: str = "+0%"
    pitch: str = "+0Hz"


class NarrationRequest(BaseModel):
    segments: List[NarrationSegment]
    gap_ms: int = 250  # 段间静音（毫秒），edge-tts 不直接生成静音，用间隔实现


# ---------- 接口 ----------
@app.get("/api/voices")
async def get_voices():
    """返回全部可用音色，前端用于下拉选择。"""
    try:
        voices = await list_voices()
        # 只保留中文相关 + 默认推荐在前，避免一次返回上百个声音
        cn = [v for v in voices if str(v.get("Locale", "")).lower().startswith(("zh", "cmn"))]
        others = [v for v in voices if v not in cn]
        ordered = sorted(cn, key=lambda v: (v["ShortName"] not in DEFAULT_VOICES, v["ShortName"]))
        return {"voices": ordered + others}
    except Exception as e:  # 网络失败时降级到内置默认
        return {"voices": [{"ShortName": v, "Locale": "zh", "Gender": "未知"} for v in DEFAULT_VOICES], "offline": str(e)}


@app.post("/api/parse")
async def api_parse(req: ParseRequest):
    """把原始博客文本解析成带说话人的片段。"""
    segs = parse_blog_text(req.text)
    if not segs:
        raise HTTPException(status_code=400, detail="未能从文本中解析出任何片段，请按『名字：内容』格式填写")
    return {"segments": [s.to_dict() for s in segs]}


@app.post("/api/tts")
async def api_tts(req: TTSRequest):
    """合成单段语音，返回 MP3（用于逐段试听）。"""
    try:
        mp3 = await synthesize(req.text, req.voice, req.rate, req.pitch)
        return Response(content=mp3, media_type="audio/mpeg", headers={"Content-Disposition": "inline; filename=segment.mp3"})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"语音合成失败：{e}")


@app.post("/api/narrate")
async def api_narrate(req: NarrationRequest):
    """逐段合成并合并为一个 MP3 文件返回。"""
    if not req.segments:
        raise HTTPException(status_code=400, detail="没有可合成的片段")

    gap_bytes = _silence_mp3(req.gap_ms)
    chunks: List[bytes] = []
    errors: List[str] = []

    # 串行合成，避免短时间内打太多请求触发 edge-tts 限流
    for idx, seg in enumerate(req.segments):
        try:
            mp3 = await synthesize(seg.text, seg.voice, seg.rate, seg.pitch)
            chunks.append(mp3)
            if idx < len(req.segments) - 1:
                chunks.append(gap_bytes)
        except Exception as e:
            # 警告走 ASCII（HTTP header 只能 latin-1），非 ASCII 字符替换掉
            msg = str(e).encode("ascii", "replace").decode("ascii")
            speaker = seg.speaker.encode("ascii", "replace").decode("ascii")
            errors.append(f"segment {idx + 1} ({speaker}): {msg}")

    if not chunks:
        raise HTTPException(status_code=502, detail="；".join(errors) or "全部片段合成失败")

    merged = merge_mp3(chunks)
    headers = {
        "Content-Disposition": 'attachment; filename="narration.mp3"',
        "X-Warnings": "; ".join(errors),
    }
    return Response(content=merged, media_type="audio/mpeg", headers=headers)


def _silence_mp3(ms: int) -> bytes:
    """生成一段指定时长的静音 MP3（用 128kbps 静音帧）。"""
    # 128kbps 下每帧 144 字节，时长约 26ms；这里用一个已知有效的静音帧重复
    silence_frame = bytes.fromhex(
        "fffb9000000000000000000000000000000000000000000000000000"
        "00000000000000000000000000000000000000000000000000000000"
    )
    frame_ms = 26.12
    n = max(1, int(ms / frame_ms))
    return silence_frame * n


# ---------- 静态前端 ----------
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
