"""Small local HTTP adapter around report_flow.generate_report()."""

from __future__ import annotations

import hmac
import json
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from .report_flow import ReportError, generate_report, load_local_env, normalize_source


JOBS: dict[str, dict] = {}
LOCK = threading.Lock()
POOL = ThreadPoolExecutor(max_workers=1)


def run_job(job_id: str, source: str, count: int) -> None:
    with LOCK:
        JOBS[job_id]["status"] = "running"
    try:
        result = generate_report(source, count)
        update = {"status": "completed", **result}
    except Exception as exc:
        update = {"status": "failed", "error": str(exc) if isinstance(exc, (ValueError, ReportError)) else "보고서 생성 중 오류가 발생했습니다."}
    with LOCK:
        JOBS[job_id].update(update)


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authorized(self) -> bool:
        secret = os.environ["REPORT_API_TOKEN"]
        provided = self.headers.get("Authorization", "")
        if not hmac.compare_digest(provided, "Bearer " + secret):
            self.send_json(401, {"error": "인증 실패"})
            return False
        return True

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self.send_json(200, {"status": "ok"})
            return
        if not self.authorized():
            return
        match = path.split("/")
        if len(match) != 3 or match[1] != "reports":
            self.send_json(404, {"error": "경로 없음"})
            return
        with LOCK:
            job = JOBS.get(match[2])
            snapshot = job.copy() if job else None
        if snapshot is None:
            self.send_json(404, {"error": "작업 없음"})
        else:
            self.send_json(200, snapshot)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/reports":
            self.send_json(404, {"error": "경로 없음"})
            return
        if not self.authorized():
            return
        if not os.getenv("OPENAI_API_KEY"):
            self.send_json(503, {"error": "OPENAI_API_KEY가 설정되지 않았습니다."})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 1 <= size <= 4096:
                raise ValueError("요청 크기가 유효하지 않습니다.")
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError("JSON 객체를 보내야 합니다.")
            source = normalize_source(data.get("source"))
            count = data.get("count", 5)
            if type(count) is not int or not 1 <= count <= 10:
                raise ValueError("count는 1~10의 정수여야 합니다.")
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json(400, {"error": str(exc)})
            return
        job_id = uuid.uuid4().hex
        with LOCK:
            JOBS[job_id] = {"id": job_id, "source": source, "status": "queued"}
        POOL.submit(run_job, job_id, source, count)
        self.send_json(202, {"id": job_id, "status": "queued", "status_path": f"/reports/{job_id}"})


def serve() -> None:
    load_local_env()
    if not os.getenv("REPORT_API_TOKEN"):
        raise SystemExit("REPORT_API_TOKEN 환경변수가 필요합니다.")
    host = os.getenv("REPORT_API_HOST", "127.0.0.1")
    port = int(os.getenv("REPORT_API_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Report API listening on http://{host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    serve()
