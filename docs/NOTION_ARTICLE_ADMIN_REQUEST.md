# Notion 뉴스레터 하위 페이지 자동 작성: 관리자 요청 사항

> 2026-11-15 기준. 새 뉴스레터 **한 호당 하위 페이지 하나**를 [【뉴스레터】GitHub Trending](https://app.notion.com/p/GitHub-Trending-4197cfd0ca688017a33bc594146e02d4) 아래에 작성한다. 상위 페이지 ID는 `4197cfd0ca688017a33bc594146e02d4`다. 기존 페이지의 본문에 덧붙이거나 기사마다 별도 페이지를 만들지 않는다.

연결된 ChatGPT Notion 도구로 이 상위 페이지와 기존 [한국어 조사 하위 페이지](https://app.notion.com/p/4127cfd0ca6880479087c01740cf5465)를 읽었다. 이는 **ChatGPT 연결의 읽기 성공**만 뜻한다. 배포할 Python 프로그램의 Notion API 자격 증명, 하위 페이지 생성·수정 권한, 상위 페이지의 공개 범위는 아직 확인되지 않았다.

## 관리자에게 요청할 설정과 답변

1. **자동화용 연결:** 이 워크스페이스에서 운영할 팀 소유 Notion *내부 연결*을 만들거나 기존 연결의 이름과 관리자를 지정해 주세요. 배포된 GitHub Actions 또는 Cloud Run Jobs에서 사용할 연결이다. ChatGPT Notion 플러그인의 로그인과는 별개다. 조직 정책상 연결 생성·설치 승인이 필요하면 승인 담당자도 지정해 주세요. [Notion 인증 안내](https://developers.notion.com/guides/authorization/overview)
2. **기능 권한:** 새 하위 페이지 작성에는 `Insert content`, 상위 페이지·기존 하위 페이지 조회와 중복 확인에는 `Read content`를 허용해 주세요. 발행 후 오탈자 수정이나 재실행 시 기존 페이지 갱신을 원한다면 `Update content`도 허용해 주세요. 필요 없는 댓글·사용자 정보 권한은 요청하지 않습니다. [Notion 연결 기능 권한](https://developers.notion.com/reference/capabilities)
3. **상위 페이지 연결:** 위 `【뉴스레터】GitHub Trending` 페이지의 `••• → Connections/Add connections`에서 해당 내부 연결을 추가해 주세요. 연결이 지정 페이지와 하위 페이지에 접근하는지 확인해 주세요. 상위 페이지가 다른 워크스페이스로 이동하거나 연결이 제거될 때 누가 관리할지도 정해 주세요. [페이지에 연결 추가](https://www.notion.com/help/add-and-manage-connections-with-the-api)
4. **비밀값 전달:** 내부 연결 토큰을 GitHub Actions Secrets의 승인된 비밀 저장소에 **관리자가 직접 등록**하거나 보안 담당자가 등록할 수 있도록 해 주세요. 토큰을 Markdown, 저장소, 일반 채팅에 적지 않습니다. 토큰 교체·폐기 담당자도 지정해 주세요. [Notion API 자격 증명 안내](https://developers.notion.com/guides/authorization/overview)
5. **공개 및 승인:** 상위 페이지가 `누구나 링크로 보기` 또는 Notion Site로 공개되어 있는지, 하위 페이지를 만들면 즉시 누구에게 보이는지 확인해 주세요. Notion은 하위 페이지에 상위 페이지의 권한을 상속하며, 공개된 Site의 하위 페이지도 기본적으로 공개됩니다. 따라서 검토 전 초안은 이 페이지 아래에 만들지 않고, **승인된 완성본만 생성**하는 방식을 제안합니다. Notion 내부에서 초안 검토가 필요하다면 별도의 비공개 검토 위치와 담당자를 지정해 주세요. 최종 승인자, 승인 기록 위치, 공개 시각도 알려주세요. [공유 권한](https://www.notion.com/help/sharing-and-permissions), [Notion Site 공개 방식](https://www.notion.com/help/public-pages-and-web-publishing)
6. **페이지 형식:** 하위 페이지의 제목 규칙(예: `テックニュースレター — YYYY-MM-DD`), 표시 날짜·주차, 일본어 본문 템플릿, 기사 순서·분량, 출처 링크, 표·이미지 사용 기준을 알려주세요. 기존 [일본어 GitHub 시범본](EXAMPLES.md)을 형식 기준으로 삼을지도 확인해 주세요. 이 상위 페이지에는 현재 한국어 조사 보고서가 있으므로, 일본어 완성본의 형식은 별도 확정이 필요합니다.
7. **재실행·수정:** 같은 기준 주차의 작업을 다시 실행했을 때 기존 하위 페이지를 갱신할지, 새 페이지를 만들지 정해 주세요. 중복 판별 기준은 `뉴스레터 종류 + 토요일 09:00 KST 집계 종료 시각`을 제안합니다. 발행 후 정정·철회 권한과 담당자도 지정해 주세요.
8. **완료 확인:** 생성된 페이지의 ID·URL을 어디에 기록할지, 부모 페이지 ID·제목·본문·출처 링크·공개 범위를 누가 확인할지 정해 주세요. 별도 비공개 시험 위치에서 권한을 먼저 확인하고, 이 상위 페이지에는 승인된 시범호를 한 번 작성해 최종 확인하는 방식을 제안합니다.

## 이미 확정된 내용과 남은 결정

- **상위 위치:** 사용자가 위 `【뉴스레터】GitHub Trending` 페이지를 지정했다.
- **페이지 단위:** 뉴스레터 한 호당 하위 페이지 하나다.
- **집계 기준:** 토요일 09:00 KST다. 실제 공개 시각은 아직 미정이다.
- **독자·산출물:** 주 독자는 개발자이며 일본어 뉴스레터 완성본을 원한다. AI 뉴스는 호당 7건으로 계획한다.
- **미확인:** 배포용 내부 연결, API 권한과 토큰 저장, 부모 페이지 공개 상태, 승인 담당자, 본문 형식, 재실행 처리.

## 연결 확인 절차

1. 워크스페이스 소유자가 내부 연결을 만들고 `Read content`·`Insert content`, 필요 시 `Update content`를 부여한다. 팀이 운영할 연결 이름과 담당자를 기록한다. [Notion 인증 안내](https://developers.notion.com/guides/authorization/overview)
2. 상위 페이지의 `••• → Connections/Add connections`에서 이 연결을 추가한다. 연결은 해당 페이지와 하위 페이지에 접근한다. 조직 정책으로 연결 설치·추가가 제한돼 있다면 워크스페이스 관리자에게 허용을 요청한다. [Notion 연결 관리](https://www.notion.com/help/add-and-manage-connections-with-the-api)
3. 토큰을 선택한 배포 환경의 비밀 저장소에 등록하고 읽기 호출을 시험한다. 현재 ChatGPT 플러그인 연결은 배포된 Python 프로그램의 인증으로 사용할 수 없다.
4. 공개되지 않은 별도 시험 위치에서 페이지 생성을 시험한다. 승인된 시범호만 지정 상위 페이지에 생성하고 반환된 페이지 ID·URL·본문·출처 링크·공개 상태를 확인한다.

2026-11-14의 로그인 없는 HTTP GET에서는 일반 Notion HTML만 확인했다. 2026-11-15에는 연결된 ChatGPT Notion 도구로 상위 페이지와 기존 하위 페이지를 읽었다. 어느 확인도 배포용 연결의 **쓰기 권한**이나 외부 공개 상태를 증명하지 않는다.

## 관리자에게 보낼 요청문

> 매주 완성된 일본어 뉴스레터를 [【뉴스레터】GitHub Trending](https://app.notion.com/p/GitHub-Trending-4197cfd0ca688017a33bc594146e02d4) 아래에 **호당 하위 페이지 하나**로 자동 작성하려고 합니다. GitHub Actions 또는 Cloud Run Jobs에서 사용할 팀 소유 Notion 내부 연결을 만들고, 이 상위 페이지의 `Connections`에 추가해 주세요. 연결에는 새 페이지 작성을 위한 `Insert content`, 조회·중복 확인을 위한 `Read content`, 발행 후 수정을 허용할 경우 `Update content` 권한이 필요합니다. 토큰은 배포 환경의 비밀 저장소에 직접 등록해 주세요. 상위 페이지와 새 하위 페이지의 공개 범위, 최종 승인자·공개 시각, 일본어 페이지 제목·본문 형식, 재실행 시 기존 페이지 수정 여부도 알려주세요. 공개 부모의 하위 페이지가 즉시 공개된다면 승인된 완성본만 이 위치에 생성하고, 시험·검토용으로 별도 비공개 위치를 지정해 주세요.
