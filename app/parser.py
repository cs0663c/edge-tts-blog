"""多人博客文本解析：把 "名字A：xxxx\\n名字B：xxxx" 拆成带说话人的片段。"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class Segment:
    speaker: str
    text: str
    voice: str = ""  # 由前端在解析后为每个说话人分配

    def to_dict(self) -> dict:
        return asdict(self)


# 匹配 "名字：内容" 或 "名字:内容"，名字里允许中英文、数字、空格
_LINE_RE = re.compile(r"^\s*([^：:]{1,40}?)\s*[：:]\s*(.+?)\s*$")


def parse_blog_text(raw: str) -> List[Segment]:
    """解析多人博客文本。

    支持的书写方式（每行一条，也允许用换行 / 中文分号 / 句号后另起说话人）：
      名字A：你好世界
      名字B: 今天天气不错
    若某行没有 "名字：" 前缀，则归入上一个说话人，作为其内容续写。
    """
    segments: List[Segment] = []
    current: Segment | None = None

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = _LINE_RE.match(line)
        if m:
            speaker, text = m.group(1).strip(), m.group(2).strip()
            if not text:
                continue
            current = Segment(speaker=speaker, text=text)
            segments.append(current)
        else:
            # 没有名字前缀，追加到上一段
            if current is None:
                current = Segment(speaker="旁白", text=line)
                segments.append(current)
            else:
                current.text = f"{current.text} {line}"

    return segments
