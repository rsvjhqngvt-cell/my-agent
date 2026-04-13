"""잘린(truncated) 리포트를 복구하는 일회성 스크립트.

기존 content를 Claude에게 보내서 잘린 기업 섹션을 완성 요청.
뉴스 섹션은 유지하고 기업 섹션만 재생성.
"""
import json
import os
import time
from anthropic import Anthropic

client = Anthropic()


def find_truncated_reports():
    index_path = "reports/index.json"
    with open(index_path, "r", encoding="utf-8") as f:
        dates = json.load(f)

    truncated = []
    for d in dates:
        path = f"reports/{d}.json"
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "=== END ===" not in data["content"]:
            truncated.append(d)
    return truncated


def repair_report(date_str):
    path = f"reports/{date_str}.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    content = data["content"]

    prompt = f"""아래는 M&A 인텔리전스 리포트인데, 기업 섹션이 중간에 잘렸습니다.
잘린 부분부터 이어서 완성해주세요.

## 규칙:
1. 기존에 작성된 내용은 절대 수정하지 마세요
2. 잘린 마지막 줄부터 이어서 작성하세요
3. 각 기업은 반드시 ���량/시너지/S/W/O/T/주의/홈페이지 항목을 모두 포함해야 합니다
4. 홈페이지 URL을 모르면 https://www.google.com/search?q=기업명 형태로 작성
5. S/W/O/T/시사점/역량/시너지/주의 항목은 각각 한 문장(50자 이내)으로 작성
6. 마지막에 반드시 === END === 를 붙이세요
7. 기존 내용 전체 + 이어쓴 부분을 합쳐서 출력하세요

## 잘린 리포트 전문:
{content}

위 내용 전체를 포함하여, 잘린 부분을 이어서 완성한 전체 리포트를 출력하세요."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )
    result = message.content[0].text

    # === END === 마커 확인
    if "=== END ===" not in result:
        result = result.rstrip() + "\n\n=== END ==="

    # 기존 뉴스 섹션이 유지되었는지 확인 (뉴스1이 있어야 함)
    if "[뉴스1]" not in result:
        print(f"  [경고] {date_str}: 뉴스 섹션이 사라짐 — 원본 유지")
        return False

    # 저장
    data["content"] = result
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return True


def main():
    truncated = find_truncated_reports()
    print(f"잘린 리포트 {len(truncated)}개 발견: {truncated}")

    for i, d in enumerate(truncated):
        print(f"\n[{i+1}/{len(truncated)}] {d} 복구 중...")
        try:
            ok = repair_report(d)
            if ok:
                print(f"  [완료] {d} 복구 성공")
            else:
                print(f"  [실패] {d} 복구 실패 — 원본 유지")
        except Exception as e:
            print(f"  [오류] {d}: {e}")

        # API rate limit 대비
        if i < len(truncated) - 1:
            time.sleep(2)

    print("\n=== 복구 완료 ===")


if __name__ == "__main__":
    main()
