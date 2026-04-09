# .collab/ — Claude Code ↔ Codex CLI 협업 보드

이 디렉토리는 두 AI 에이전트(Claude Code, Codex CLI)가 같은 프로젝트에서 협업할 때
서로의 작업을 핸드오프·검증하는 공용 공간입니다.

## 파일 구성

| 파일 | 용도 |
|------|------|
| `handoff.md` | 작업 요청·응답·검증 게시판 (양방향, 최신순) |
| `decisions.md` | 두 에이전트가 합의한 설계/방향 결정 로그 |
| `README.md` | 이 문서 (사람용 설명) |

## 사용 방법

### 사용자가 할 일
1. Claude Code 또는 Codex CLI 한쪽에서 작업 지시
2. 작업 끝나면 → "다른 쪽에 검증 받아줘" 라고 말하기
3. 또는 "이 작업은 Codex가 더 잘할 것 같으니 핸드오프해줘"

### 에이전트가 할 일 (자동)
- 작업 시작 시: `handoff.md` 상위 항목 읽기
- 작업 종료 시: 변경 요약 + 검증 요청을 `handoff.md` 맨 위에 추가
- 충돌 가능성 있으면 사용자에게 먼저 보고

## 협업 시나리오 예시

### 시나리오 1: 코드 작성 → 교차 리뷰
```
사용자 → Claude:  "agent.py에 새 기능 X 추가해줘"
Claude:          [구현 후 handoff.md에 'review-request' 등록]
사용자 → Codex:  "방금 Claude가 한 작업 검증해줘"
Codex:           [handoff.md 읽고 → 코드 분석 → 'review-response' 작성]
```

### 시나리오 2: 작업 분할
```
사용자 → Claude:  "PPT 생성기 리팩토링해줘. 알고리즘 부분은 Codex가 처리"
Claude:          [구조 설계 후 'task-handoff'로 알고리즘 부분 명세를 Codex에게]
Codex:           [명세 보고 알고리즘 구현 → 'task-handoff' 응답]
Claude:          [통합 → 최종 commit]
```

### 시나리오 3: 의견 충돌
```
한쪽이 작성 → 다른쪽이 반대 → decisions.md에 양측 입장과 최종 결정 기록
→ 사용자가 최종 판단
```

## 규칙
- **핸드오프 항목은 항상 파일 맨 위에 추가** (최신순 정렬)
- 같은 파일 동시 수정 금지 — `handoff.md`에 "작업 중" 표시
- 양쪽 에이전트는 작업 후 commit & push (사용자 별도 요청 불필요)
