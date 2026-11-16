"""Explicitly publish a reviewed Markdown newsletter as one Notion child page."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from .report_flow import load_local_env

NOTION_VERSION = "2026-03-11"
API_ROOT = "https://api.notion.com/v1"


class NotionPublishError(RuntimeError):
    pass


def title_from_markdown(markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# ") and line[2:].strip():
            return line[2:].strip()
    raise NotionPublishError("제목을 지정하거나 Markdown 첫 줄에 '# 제목'을 작성하세요.")


def _page_id(value: str) -> str:
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError) as exc:
        raise NotionPublishError("올바른 Notion 상위 페이지 ID가 필요합니다.") from exc


class NotionClient:
    def __init__(self, token: str):
        if not token:
            raise NotionPublishError("NOTION_API_KEY가 설정되지 않았습니다.")
        self.token = token

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            API_ROOT + path,
            data=data,
            headers={
                "Authorization": "Bearer " + self.token,
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
            method=method,
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    return json.load(response)
            except urllib.error.HTTPError as exc:
                if method == "GET" and exc.code in {429, 500, 502, 503, 504, 529} and attempt < 2:
                    try:
                        delay = max(0, int(exc.headers.get("Retry-After", "1")))
                    except ValueError:
                        delay = 2 ** attempt
                    exc.close()
                    time.sleep(delay)
                    continue
                code = exc.code
                exc.close()
                if code == 404 and path == "/pages":
                    raise NotionPublishError(
                        "Notion 상위 페이지를 찾을 수 없거나 이 연결에 공유되지 않았습니다 (HTTP 404). "
                        "상위 페이지의 Connections에 해당 연결을 추가했는지 확인하세요."
                    ) from exc
                raise NotionPublishError(f"Notion API 요청 실패 (HTTP {code}, {method} {path.split('?')[0]}).") from exc
            except urllib.error.URLError as exc:
                raise NotionPublishError(f"Notion API 연결 실패 ({method}). 작성 요청이었다면 상위 페이지를 확인한 뒤 재시도하세요.") from exc
        raise AssertionError("retry loop exhausted")

    def create_child(self, parent_id: str, title: str, markdown: str) -> dict:
        parent_id = _page_id(parent_id)
        if not title.strip() or not markdown.strip():
            raise NotionPublishError("제목과 Markdown 본문은 비어 있을 수 없습니다.")
        page = self._request("POST", "/pages", {
            "parent": {"type": "page_id", "page_id": parent_id},
            "properties": {"title": {"title": [{"text": {"content": title}}]}},
            "markdown": markdown,
            "markdown_version": "v2",
        })
        if page.get("object") != "page" or not page.get("id") or not page.get("url"):
            raise NotionPublishError("Notion 응답에서 생성된 페이지 ID 또는 URL을 확인할 수 없습니다.")
        if _page_id(page.get("parent", {}).get("page_id", "")) != parent_id:
            raise NotionPublishError("생성된 페이지의 상위 페이지 ID가 요청과 다릅니다.")
        return {"id": page["id"], "url": page["url"], "title": title}


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish one reviewed Markdown file below a Notion page")
    parser.add_argument("file", type=Path)
    parser.add_argument("--title", help="Notion page title; defaults to first Markdown H1")
    parser.add_argument("--language", choices=("ko", "ja"), required=True)
    parser.add_argument("--parent", help="Override parent page ID, e.g. for a private test page")
    parser.add_argument("--publish", action="store_true", help="Actually create the Notion page")
    args = parser.parse_args()
    try:
        markdown = args.file.read_text(encoding="utf-8-sig")
        if not markdown.strip():
            raise NotionPublishError("Markdown 본문은 비어 있을 수 없습니다.")
        title = args.title.strip() if args.title else title_from_markdown(markdown)
        if not title:
            raise NotionPublishError("제목은 비어 있을 수 없습니다.")
        if not args.publish:
            print(f"미리보기: {title} ({len(markdown)}자); --publish가 있어야 작성합니다.")
            return
        load_local_env()
        parent_id = args.parent or os.getenv(f"NOTION_PARENT_PAGE_ID_{args.language.upper()}", "")
        if args.language == "ko" and not parent_id:
            parent_id = os.getenv("NOTION_PARENT_PAGE_ID", "")
        parent_id = _page_id(parent_id)
        token = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN", "")
        result = NotionClient(token).create_child(parent_id, title, markdown)
        print(json.dumps(result, ensure_ascii=True))
    except (OSError, ValueError, NotionPublishError) as exc:
        parser.exit(1, f"오류: {exc}\n")


if __name__ == "__main__":
    main()
