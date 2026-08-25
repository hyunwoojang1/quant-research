"""선택된 논문 2편의 폴더 구조 생성 + PDF 다운로드 + 본문 텍스트 추출.

docx 작성을 정확한 본문 근거 위에서 하기 위해 PDF 텍스트를 *.txt 로 추출한다.
"""
from __future__ import annotations

from pathlib import Path

import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"

SELECTED = [
    {"folder": "2023_DiffusionVAE_Koa", "arxiv": "2309.00073"},
    {"folder": "2024_TransformerDRL_BlackLitterman_Sun", "arxiv": "2402.16609"},
]

SUBDIRS = ["models", "results/in_sample", "results/out_of_sample", "results/time_robustness"]


def setup_one(folder: str, arxiv: str) -> None:
    base = PAPERS / folder
    for sd in SUBDIRS:
        (base / sd).mkdir(parents=True, exist_ok=True)

    pdf_path = base / "paper.pdf"
    if not pdf_path.exists():
        url = f"https://arxiv.org/pdf/{arxiv}"
        headers = {"User-Agent": "quant-research-validator/1.0 (academic)"}
        r = requests.get(url, headers=headers, timeout=120)
        r.raise_for_status()
        pdf_path.write_bytes(r.content)
    print(f"[{folder}] PDF: {pdf_path.stat().st_size} bytes")

    # 본문 텍스트 추출 (docx 근거용; 저장은 .txt)
    txt_path = base / "_extracted_text.txt"
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, pg in enumerate(reader.pages):
        try:
            pages.append(f"\n===== PAGE {i+1} =====\n" + (pg.extract_text() or ""))
        except Exception as e:  # noqa: BLE001
            pages.append(f"\n===== PAGE {i+1} (extract error: {e}) =====\n")
    safe = "".join(pages).encode("utf-8", "replace").decode("utf-8")
    txt_path.write_text(safe, encoding="utf-8")
    print(f"[{folder}] pages={len(reader.pages)}, text chars={txt_path.stat().st_size}")


def main() -> None:
    for p in SELECTED:
        setup_one(p["folder"], p["arxiv"])


if __name__ == "__main__":
    main()
