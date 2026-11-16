# 테크 뉴스레터

한국어·영어 자료를 조사해 한국어와 일본어 주간 뉴스레터를 만드는 프로젝트다. 현재 자동화된 코드는 GitHub Trending과 GeekNews의 **한국어 조사 보고서 완성본**을 생성한다. 일본어판은 해당 보고서 내용을 그대로 번역할 예정이다. AI 뉴스 통합, 일본어 번역, Notion 자동 발행은 [계획](AI_NEWS_AUTOMATION_PLAN.md)에 남아 있다.

## 파일 안내

| 파일 | 내용 |
| --- | --- |
| [PLAN.md](PLAN.md) | 독자·뉴스 범주·수집 소스·편집 기준 |
| [AI_NEWS_AUTOMATION_PLAN.md](AI_NEWS_AUTOMATION_PLAN.md) | AI 뉴스 자동화 설계와 관리자에게 남은 질문 |
| [NOTION_ARTICLE_ADMIN_REQUEST.md](NOTION_ARTICLE_ADMIN_REQUEST.md) | Notion 하위 페이지 작성 설정과 관리자 요청문 |
| [REPORT_GUIDELINES.md](REPORT_GUIDELINES.md) | GitHub Trending·GeekNews 한국어 조사 보고서 형식 |
| [EXAMPLES.md](EXAMPLES.md) | 2026-11-08 시범 보고서와 일본어본 |
| `newsletter/report_flow.py` / `newsletter/report_api.py` | 보고서 생성 CLI / 로컬 HTTP API |
| `newsletter/notion_publish.py` | 검토 완료 Markdown 파일을 Notion 하위 페이지 하나로 발행하는 명시적 CLI |

## 현재 보고서 생성

`generate_report(source, count=5)`는 후보 수집, 자료 정리, OpenAI API를 이용한 한국어 상세 보고서 작성, Markdown 파일 저장을 수행한다. `source`는 `github` 또는 `geeknews`이며 오타 별칭 `gekknews`도 받는다. `count`는 1~10이다. 완성된 파일은 `reports/<작업 ID>/`에 저장되어 이전 결과를 덮어쓰지 않는다.

| 입력 | 수집 경로 | 주의할 점 |
| --- | --- | --- |
| `github` | [GitHub Trending 주간 화면](https://github.com/trending?since=weekly), 저장소 README·메타데이터 | 화면 순서를 따른다. 공식 순위 API가 아니므로 HTML 구조 변경에 취약하다. |
| `geeknews` | [GeekNews 공식 최신 글 RSS](https://news.hada.io/blog/geeknews_feed) | 등록 시각순 최신 글이다. 첫 화면 인기 순위·점수와 다르다. |

RSS에 원문 링크가 없는 글은 모델에 웹 검색을 요청하고, 찾지 못하면 `원문 확인 필요`로 표시하도록 지시한다. 두 경로 모두 원자료와 수치의 정확성을 사람이 검토해야 한다. [GeekNews 첫 화면 시범본](EXAMPLES.md)은 당시 화면을 조사한 별도 결과이며 RSS 자동 보고서로 취급하지 않는다.

## 실행

프로젝트 루트에서 Python 3.11 이상과 표준 라이브러리를 사용한다. [`.env.example`](../.env.example)을 프로젝트 루트의 `.env`로 복사하고 키를 입력한다. 설정 우선순위는 **프로세스 환경변수 → 프로젝트 `.env` → 작업공간 루트 `.env`**다. 로더는 `OPENAI_API_KEY`, `OPENAI_MODEL`, `REPORT_API_TOKEN`, `REPORT_API_HOST`, `REPORT_API_PORT`, `GITHUB_TOKEN`, `NOTION_API_KEY`, `NOTION_PARENT_PAGE_ID_KO`, `NOTION_PARENT_PAGE_ID_JA`만 읽는다. `OPENAI_MODEL` 기본값은 `gpt-6-astra`다.

```powershell
Copy-Item .env.example .env
# .env에 OPENAI_API_KEY와 REPORT_API_TOKEN을 설정
python -m newsletter.report_flow github
python -m newsletter.report_flow geeknews --count 5
python -m newsletter.report_api
python -m unittest discover -s tests -v
```

실제 키와 토큰은 코드·문서·명령행 예시에 기록하지 않는다. `GITHUB_TOKEN`은 GitHub API 한도에 필요할 때만 사용한다. OpenAI API 사용량에는 별도 비용이 든다.

## 로컬 HTTP API

기본 바인딩은 `127.0.0.1:8765`다. `REPORT_API_TOKEN`이 필요하고 모든 `/reports` 요청은 `Authorization: Bearer <토큰>`으로 인증한다. `/health`는 인증 없이 상태만 반환한다.

| 요청 | 결과 |
| --- | --- |
| `POST /reports`와 JSON `{"source":"github","count":5}` | 즉시 `202`, 작업 ID와 조회 경로 반환 |
| `GET /reports/{id}` | `queued` → `running` → `completed` 또는 `failed`; 완료 시 Markdown·로컬 경로 반환 |

서버는 작업을 한 번에 하나씩 실행하고 작업 상태를 메모리에 보관하므로 재시작하면 상태가 사라진다. 파일은 남는다. 이 API는 Discord Interaction 엔드포인트가 아니며 봇 어댑터·서명 검증·첨부 전송은 구현되지 않았다. 예약 배치 실행에는 HTTP 서버 대신 별도 명령형 진입점을 만들 계획이다.

## 미구현 및 운영 전 확인

- 토요일 09:00 KST로 고정한 주간 집계, 매일 후보 저장, 중복 제거, AI 뉴스 7건 선정.
- 일본어 뉴스레터 완성본과 관리자 승인 기록.
- GitHub Actions 또는 Cloud Run Jobs 예약 실행, 영구 저장소와 장애 알림.
- [지정 Notion 상위 페이지](NOTION_ARTICLE_ADMIN_REQUEST.md)에 자동 발행을 연결하는 작업. 수동 파일 발행 CLI는 구현됐으나 관리자 권한, 승인 방식, 실제 발행 검증이 필요하다.

## Notion 수동 발행 모듈

`newsletter.notion_publish`는 Markdown 파일 한 개를 언어별 상위 페이지의 하위 페이지 하나로 작성한다. `--publish`를 빼면 파일과 제목만 확인하며 API에 접근하지 않는다. 같은 제목의 하위 페이지가 있어도 재실행 시 새 페이지를 작성한다. 현재 자동 생성물은 한국어 조사 보고서 완성본이며 일본어판 생성과 두 부모 페이지의 공개 범위 확인이 남아 있어 예약 작업에 발행 명령을 연결하지 않았다.

```powershell
python -m newsletter.notion_publish reports/<작업 ID>/<파일>.md --language ko --title "승인된 한국어 제목"
python -m newsletter.notion_publish reports/<작업 ID>/<파일>.md --language ja --title "承認済みの日本語タイトル" --publish
```

실제 발행에는 `NOTION_API_KEY`와 해당 언어의 `NOTION_PARENT_PAGE_ID_KO` 또는 `NOTION_PARENT_PAGE_ID_JA`가 필요하다. 로컬에서는 `NOTION_TOKEN`을 토큰의 별칭으로, 한국어 발행에는 `NOTION_PARENT_PAGE_ID`를 부모 ID의 별칭으로 사용할 수 있다. `.env` 값에서 `=` 앞뒤 공백도 허용한다. `--parent`로 비공개 시험 페이지 ID를 지정할 수도 있다. 성공하면 생성 페이지의 ID와 URL을 출력한다. 발행 요청 중 연결이 끊기면 의도치 않은 추가 발행을 피하도록 자동 재시도하지 않으므로 상위 페이지를 확인한 뒤 다시 실행한다.

## GitHub Actions에서 한국어 보고서 발행

[`.github/workflows/notion.yml`](../.github/workflows/notion.yml)은 수동 실행(`workflow_dispatch`) 시 GitHub Trending 한국어 보고서를 생성하고 해당 언어 Notion 부모 페이지에 하위 페이지로 작성한다. 별도 `requests` 설치나 `main.py`는 사용하지 않는다. 먼저 저장소의 Actions Secrets에 `OPENAI_API_KEY`, `NOTION_TOKEN`, `NOTION_PARENT_PAGE_ID`를 등록한다. 마지막 값은 한국어 부모 페이지 ID다. 워크플로는 `NOTION_TOKEN`을 프로그램의 `NOTION_API_KEY`로 전달한다. Notion 연결에 해당 부모 페이지의 쓰기 권한이 필요하다. 일본어 번역과 일본어 부모 페이지 발행은 이 워크플로에 아직 포함되지 않았다. 재실행하면 새 페이지가 추가된다.

외부 사이트 접근 실패, GitHub API 한도, 원문 접근 제한 또는 모델 형식 오류는 현재 보고서 작업을 실패로 반환한다. 실패 자료를 확인된 사실로 채워 넣지 않는다.
