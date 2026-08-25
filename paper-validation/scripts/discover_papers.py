"""Phase 1 논문 탐색 (v2): Semantic Scholar 인용수 정렬 검색.

'최근 3년 + 인용수 있는' 논문을 찾기 위해, 최신순 arXiv 대신
Semantic Scholar bulk search 를 인용수 내림차순으로 사용한다.
퀀트 ML/파생상품 관련 쿼리 여러 개를 합쳐 dedupe 후, arXiv q-fin 논문만 추려 정렬.
결과는 reports/paper_candidates.json 으로 저장(+요약 출력).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "paper_candidates.json"

S2_BULK = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
FIELDS = "title,year,citationCount,externalIds,abstract,authors,fieldsOfStudy,publicationDate"
MIN_YEAR = 2023

# 퀀트 ML / 파생상품 모델링 관련 검색어 (q-fin.CP/MF/ST 성격)
QUERIES = [
    "deep hedging neural network derivatives",
    "deep learning option pricing",
    "rough volatility model calibration",
    "neural network implied volatility surface",
    "reinforcement learning portfolio trading",
    "machine learning stochastic volatility derivatives",
    "neural SDE financial modeling",
    "generative model financial time series",
    "transformer stock return prediction",
    "signature method finance machine learning",
]


def search(query: str) -> list[dict]:
    params = {
        "query": query,
        "fields": FIELDS,
        "year": f"{MIN_YEAR}-2026",
        "sort": "citationCount:desc",
    }
    for attempt in range(5):
        r = requests.get(S2_BULK, params=params, timeout=60)
        if r.status_code == 429:
            time.sleep(4 * (attempt + 1))
            continue
        if r.status_code != 200:
            return []
        return r.json().get("data", []) or []
    return []


def is_qfin_arxiv(p: dict) -> bool:
    ext = p.get("externalIds") or {}
    if "ArXiv" not in ext:
        return False
    fos = p.get("fieldsOfStudy") or []
    # arXiv 이고 경제/수학/CS 계열이면 후보 (q-fin 직접 태그는 S2 에 없음)
    allowed = {"Economics", "Mathematics", "Computer Science", "Business"}
    return not fos or bool(allowed.intersection(fos))


def main() -> None:
    pool: dict[str, dict] = {}
    for q in QUERIES:
        for p in search(q):
            pid = p.get("paperId")
            if not pid or pid in pool:
                continue
            if (p.get("year") or 0) < MIN_YEAR:
                continue
            if not is_qfin_arxiv(p):
                continue
            pool[pid] = p
        time.sleep(1.5)

    papers = list(pool.values())
    # 관련성 키워드(파생상품/ML)로 잡음 제거
    KW = [
        "deep", "neural", "machine learning", "reinforcement", "transformer",
        "gan", "generative", "diffusion", "hedging", "option", "derivative",
        "volatility", "rough", "sde", "calibration", "pricing", "lstm",
        "signature", "portfolio", "trading", "forecast", "stochastic",
    ]

    def relevance(p: dict) -> int:
        text = ((p.get("title") or "") + " " + (p.get("abstract") or "")).lower()
        return sum(1 for k in KW if k in text)

    rows = []
    for p in papers:
        rel = relevance(p)
        if rel < 2:  # 금융/ML 무관 논문 제거
            continue
        rows.append(
            {
                "arxiv_id": (p.get("externalIds") or {}).get("ArXiv"),
                "title": " ".join((p.get("title") or "").split()),
                "year": p.get("year"),
                "date": p.get("publicationDate"),
                "citations": p.get("citationCount"),
                "authors": [a.get("name") for a in (p.get("authors") or [])][:4],
                "fieldsOfStudy": p.get("fieldsOfStudy"),
                "relevance": rel,
                "abstract": " ".join((p.get("abstract") or "").split()),
            }
        )

    rows.sort(key=lambda r: (r["citations"] or 0, r["relevance"]), reverse=True)
    top = rows[:25]
    OUT.write_text(json.dumps(top, ensure_ascii=False, indent=1), encoding="utf-8")

    # 콘솔 요약(아스키 only 로 인코딩 안전)
    print(f"saved {len(top)} candidates -> {OUT}")
    for i, r in enumerate(top, 1):
        title = r["title"][:80]
        print(f"{i:2d}. [{r['citations']}c|{r['year']}] {r['arxiv_id']} | {title}")


if __name__ == "__main__":
    main()
