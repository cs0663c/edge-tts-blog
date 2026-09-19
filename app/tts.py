"""edge-tts 封装：单段合成与多段 MP3 合并。"""
from __future__ import annotations

import io
from typing import List

import edge_tts

# 常用中文音色（仅作前端默认推荐，完整列表走 /api/voices）
DEFAULT_VOICES = [
    "zh-CN-XiaoxiaoNeural",
    "zh-CN-YunxiNeural",
    "zh-CN-XiaoyiNeural",
    "zh-CN-YunyangNeural",
    "zh-CN-XiaochenNeural",
    "zh-CN-YunjianNeural",
    "zh-HK-HiuMaanNeural",
    "zh-HK-WanLungNeural",
    "zh-TW-HsiaoChenNeural",
    "zh-TW-YunJheNeural",
]


async def synthesize(text: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz") -> bytes:
    """合成单段语音，返回 MP3 字节流。"""
    buf = io.BytesIO()
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


def merge_mp3(chunks: List[bytes]) -> bytes:
    """把多段 MP3 字节流直接拼接为一个 MP3。

    edge-tts 输出的是标准 MPEG Audio 帧流，帧之间相互独立，直接字节级
    拼接即可被绝大多数播放器（浏览器 / VLC / ffplay）正确解码，
    无需引入 ffmpeg，保持镜像轻量且跨架构无原生依赖。
    """
    return b"".join(chunks)


async def list_voices() -> list:
    """返回 edge-tts 全部可用音色。"""
    return await edge_tts.list_voices()
