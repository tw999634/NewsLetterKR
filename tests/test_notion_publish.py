import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from newsletter.notion_publish import NotionClient, NotionPublishError, main, title_from_markdown


PARENT = "4197cfd0-ca68-8017-a33b-c594146e02d4"
CHILD = "4127cfd0-ca68-8047-9087-c01740cf5465"


class NotionPublishTests(unittest.TestCase):
    def test_title_comes_from_first_markdown_heading(self):
        self.assertEqual(title_from_markdown("intro\n# 한국어 보고서\n\n본문"), "한국어 보고서")
        with self.assertRaises(NotionPublishError):
            title_from_markdown("본문만 있음")

    def test_create_sends_markdown_and_returns_page_link(self):
        client = NotionClient("test-token")
        with patch.object(client, "_request", return_value={
            "object": "page", "id": CHILD, "url": "https://app.notion.com/p/child", "parent": {"page_id": PARENT}
        }) as request:
            result = client.create_child(PARENT, "Weekly 1", "# Hello\n\n[Source](https://example.org)")
        self.assertEqual(result["id"], CHILD)
        self.assertEqual(request.call_args.args[:2], ("POST", "/pages"))
        body = request.call_args.args[2]
        self.assertEqual(body["parent"]["page_id"], PARENT)
        self.assertEqual(body["markdown_version"], "v2")
        self.assertIn("[Source]", body["markdown"])

    def test_same_title_is_allowed_for_new_issue_run(self):
        client = NotionClient("test-token")
        with patch.object(client, "_request", return_value={
            "object": "page", "id": CHILD, "url": "https://app.notion.com/p/child", "parent": {"page_id": PARENT}
        }) as request:
            client.create_child(PARENT, "Weekly 1", "# Hello")
            client.create_child(PARENT, "Weekly 1", "# Hello")
        self.assertEqual(request.call_count, 2)
        self.assertTrue(all(call.args[0] == "POST" for call in request.call_args_list))

    def test_preview_does_not_need_token_or_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "issue.md"
            path.write_text("# Hello", encoding="utf-8")
            output = io.StringIO()
            with patch("sys.argv", ["notion_publish", str(path), "--language", "ko", "--title", "Weekly 1"]), patch(
                "newsletter.notion_publish.NotionClient"
            ) as client, redirect_stdout(output):
                main()
            client.assert_not_called()
            self.assertIn("미리보기", output.getvalue())


if __name__ == "__main__":
    unittest.main()
