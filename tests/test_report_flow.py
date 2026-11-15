import json
import os
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from newsletter.report_api import Handler
from newsletter.report_flow import _guidelines, load_local_env, normalize_source, parse_geeknews, parse_github


class ReportFlowTests(unittest.TestCase):
    def test_each_source_uses_only_its_own_guidelines(self):
        github = _guidelines("github")
        geeknews = _guidelines("geeknews")
        self.assertIn("GitHub Trending 주간 조사", github)
        self.assertNotIn("GeekNews 조사 보고서 작성 지침", github)
        self.assertIn("GeekNews 조사 보고서 작성 지침", geeknews)
        self.assertNotIn("GitHub Trending 주간 조사", geeknews)

    def test_github_order_and_numbers_come_from_trending_page(self):
        html = '''
        <article class="Box-row"><h2 class="h3"><a href="/a/first">a / first</a></h2>
        <p class="col-9">First project</p><span itemprop="programmingLanguage">Python</span>
        <a href="/a/first/stargazers"><svg></svg>1,234</a>
        <span>5 stars this week</span></article>
        <article class="Box-row"><h2 class="h3"><a href="/b/second">b / second</a></h2>
        <span itemprop="programmingLanguage">Rust</span>
        <a href="/b/second/stargazers">9,999</a><span>50 stars this week</span></article>
        '''
        items = parse_github(html, 2)
        self.assertEqual([item.title for item in items], ["a/first", "b/second"])
        self.assertEqual((items[0].stars, items[0].weekly_stars), ("1,234", "5"))

    def test_geeknews_feed_is_chronological_and_alias_is_accepted(self):
        xml = '''<feed xmlns="http://www.w3.org/2005/Atom">
        <entry><title>Newest</title><id>https://news.hada.io/topic?id=2</id>
        <published>2026-11-11T12:00:00+09:00</published><content type="html">&lt;p&gt;New&lt;/p&gt;</content></entry>
        <entry><title>Older</title><id>https://news.hada.io/topic?id=1</id>
        <published>2026-11-11T11:00:00+09:00</published></entry></feed>'''
        self.assertEqual(normalize_source("gekknews"), "geeknews")
        self.assertEqual([item.title for item in parse_geeknews(xml, 2)], ["Newest", "Older"])

    def test_api_auth_and_async_result(self):
        with patch.dict(os.environ, {"REPORT_API_TOKEN": "test-token", "OPENAI_API_KEY": "test-key"}), patch(
            "newsletter.report_api.generate_report",
            return_value={"source": "geeknews", "path": "report.md", "markdown": "# draft"},
        ):
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with self.assertRaises(urllib.error.HTTPError) as rejected:
                    urllib.request.urlopen(urllib.request.Request(base + "/reports", data=b"{}"))
                self.assertEqual(rejected.exception.code, 401)
                rejected.exception.close()
                request = urllib.request.Request(
                    base + "/reports",
                    data=json.dumps({"source": "gekknews"}).encode(),
                    headers={"Authorization": "Bearer test-token", "Content-Type": "application/json"},
                )
                with urllib.request.urlopen(request) as response:
                    self.assertEqual(response.status, 202)
                    accepted = json.load(response)
                for _ in range(50):
                    request = urllib.request.Request(
                        base + accepted["status_path"],
                        headers={"Authorization": "Bearer test-token"},
                    )
                    with urllib.request.urlopen(request) as response:
                        job = json.load(response)
                    if job["status"] == "completed":
                        break
                    time.sleep(0.02)
                self.assertEqual(job["source"], "geeknews")
                self.assertEqual(job["markdown"], "# draft")
            finally:
                server.shutdown()
                server.server_close()


class EnvLoaderTests(unittest.TestCase):
    def test_project_file_precedes_workspace_file_and_process_value_wins(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            project = workspace / "newsletter"
            project.mkdir()
            (workspace / ".env").write_text(
                "OPENAI_API_KEY=root-key\nREPORT_API_TOKEN=root-token\nGITHUB_TOKEN=root-github\n",
                encoding="utf-8",
            )
            (project / ".env").write_text(
                "# local settings\nexport OPENAI_API_KEY='project-key'\nOPENAI_MODEL=project-model\nOTHER_SECRET=ignored\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"OPENAI_MODEL": "process-model"}, clear=True):
                load_local_env(project)
                self.assertEqual(os.environ["OPENAI_API_KEY"], "project-key")
                self.assertEqual(os.environ["REPORT_API_TOKEN"], "root-token")
                self.assertEqual(os.environ["GITHUB_TOKEN"], "root-github")
                self.assertEqual(os.environ["OPENAI_MODEL"], "process-model")
                self.assertNotIn("OTHER_SECRET", os.environ)

    def test_quoted_hash_and_empty_project_value(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            project = workspace / "newsletter"
            project.mkdir()
            (workspace / ".env").write_text("REPORT_API_TOKEN=fallback-token\n", encoding="utf-8")
            (project / ".env").write_text(
                'OPENAI_API_KEY="sample#key" # comment\nREPORT_API_TOKEN=\n', encoding="utf-8"
            )
            with patch.dict(os.environ, {}, clear=True):
                load_local_env(project)
                self.assertEqual(os.environ["OPENAI_API_KEY"], "sample#key")
                self.assertEqual(os.environ["REPORT_API_TOKEN"], "fallback-token")


if __name__ == "__main__":
    unittest.main()
