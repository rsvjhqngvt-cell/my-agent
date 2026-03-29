import os
import json
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from anthropic import Anthropic
from datetime import date, datetime

client = Anthropic()

ISU_SYSTEM_PROFILE = """
이수시스템(ISU SYSTEM)은 다음 솔루션을 보유한 IT 기업입니다:
- AI: 챗봇, HR AI Package, AI 플랫폼, AI 이력서 분석
- 디지털 서비스: ERP 솔루션, RPA, Smart Root
- ESG: ESG 데이터 플랫폼 (지표관리, 공급망관리)
- HR: Smart HR, WORKUP, HR-Tong (500개 이상 기업 구축 경험)
- 안전: Smart Plant, Smart & Safety, BizPTT (산업현장 안전관리)
- 클라우드 인프라: Cloud Platform

현재 M&A를 통해 사업 시너지를 낼 수 있는 기업을 탐색 중입니다.
"""

NEWS_SOURCES = [
    {
        "name": "전자신문",
        "url": "https://www.etnews.com/news/section.html?id1=01",
        "article_selector": "div.articleList li",
        "title_selector": "a.tit",
        "link_selector": "a.tit",
        "base_url": "https://www.etnews.com"
    },
    {
        "name": "ZDNet Korea",
        "url": "https://zdnet.co.kr/news/?lstcode=0000",
        "article_selector": "div.newsInfoCont",
        "title_selector": "strong.tit",
        "link_selector": "a",
        "base_url": "https://zdnet.co.kr"
    },
    {
        "name": "IT조선",
        "url": "https://it.chosun.com/news/articleList.html?sc_section_code=S1N1",
        "article_selector": "div.view-cont",
        "title_selector": "a",
        "link_selector": "a",
        "base_url": "https://it.chosun.com"
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def crawl_news():
    all_news = []
    for source in NEWS_SOURCES:
        try:
            response = requests.get(source["url"], headers=HEADERS, timeout=10)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "lxml")
            articles = soup.select(source["article_selector"])[:10]
            for article in articles:
                title_el = article.select_one(source["title_selector"])
                link_el = article.select_one(source["link_selector"])
                if title_el and link_el:
                    title = title_el.get_text(strip=True)
                    href = link_el.get("href", "")
                    if href and not href.startswith("http"):
                        href = source["base_url"] + href
                    if title:
                        all_news.append({"source": source["name"], "title": title, "url": href})
            print(f"[크롤링 완료] {source['name']}: {len(articles)}건")
        except Exception as e:
            print(f"[크롤링 실패] {source['name']}: {e}")
    return all_news


def analyze_with_claude(news_list):
    news_text = "\n".join(
        [f"- [{item['source']}] {item['title']}" for item in news_list]
    )

    # Claude가 반드시 완성하도록 assistant turn prefill 사용
    system = "당신은 IT 기업 M&A 전문 컨설턴트입니다. 주어진 형식을 반드시 끝까지 빠짐없이 완성하세요. === END === 마커로 반드시 끝내세요."

    user_prompt = f"""아래 의뢰 기업 정보와 뉴스를 바탕으로, 지정된 형식을 끝까지 완성하세요.
각 항목은 반드시 한 문장(50자 이내)으로만 작성하세요.

## 의뢰 기업
{ISU_SYSTEM_PROFILE}

## 오늘의 IT 뉴스
{news_text}

## 출력 (아래 형식 그대로 완성, === END === 까지 반드시 작성)

[뉴스1] 뉴스제목
관련솔루션:
S:
W:
O:
T:
시사점:

[뉴스2] 뉴스제목
관련솔루션:
S:
W:
O:
T:
시사점:

[뉴스3] 뉴스제목
관련솔루션:
S:
W:
O:
T:
시사점:

[기업1] 기업명 | 업종 | 시총약OOO억
역량:
시너지:
S:
W:
O:
T:
주의:

[기업2] 기업명 | 업종 | 시총약OOO억
역량:
시너지:
S:
W:
O:
T:
주의:

[기업3] 기업명 | 업종 | 시총약OOO억
역량:
시너지:
S:
W:
O:
T:
주의:

=== END ==="""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=3500,
        system=system,
        messages=[{"role": "user", "content": user_prompt}]
    )

    return message.content[0].text


def save_report(report_content, news_list):
    """리포트를 JSON 파일로 저장하고 index.json을 갱신합니다."""
    today = date.today().isoformat()
    os.makedirs("reports", exist_ok=True)

    data = {
        "date": today,
        "generated_at": datetime.now().isoformat(),
        "news_count": len(news_list),
        "content": report_content
    }

    with open(f"reports/{today}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    index_path = "reports/index.json"
    index = []
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)

    if today not in index:
        index.insert(0, today)
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False)

    print(f"[리포트 저장] reports/{today}.json")


def format_to_html(text):
    lines = text.split("\n")
    html_lines = []
    in_news = False
    in_company = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("[뉴스"):
            if not in_news:
                html_lines.append('<div style="margin-bottom:8px;"><h3 style="color:#fff;background:#1a5276;padding:8px 14px;border-radius:6px;margin:0 0 12px;">📰 M&amp;A 핵심 뉴스 TOP 3</h3>')
                in_news = True
            html_lines.append(f'<div style="background:#fff;border-left:4px solid #1a5276;padding:10px 14px;margin-bottom:12px;border-radius:0 6px 6px 0;">')
            html_lines.append(f'<p style="font-weight:bold;margin:0 0 6px;color:#1a5276;">📌 {line[8:]}</p>')
        elif line.startswith("[기업"):
            if in_news:
                html_lines.append('</div></div>')
                in_news = False
            if not in_company:
                html_lines.append('<div style="margin-bottom:8px;"><h3 style="color:#fff;background:#117a65;padding:8px 14px;border-radius:6px;margin:0 0 12px;">🏢 M&amp;A 유망 기업 추천 (시총 1,000억 이하)</h3>')
                in_company = True
            else:
                html_lines.append('</div>')
            html_lines.append(f'<div style="background:#fff;border-left:4px solid #117a65;padding:10px 14px;margin-bottom:12px;border-radius:0 6px 6px 0;">')
            html_lines.append(f'<p style="font-weight:bold;margin:0 0 6px;color:#117a65;">🏢 {line[5:]}</p>')
        elif line == "=== END ===":
            if in_news or in_company:
                html_lines.append('</div></div>')
        elif line.startswith("S:"):
            html_lines.append(f'<p style="margin:3px 0;font-size:13px;"><span style="background:#d5f5e3;padding:1px 5px;border-radius:3px;font-weight:bold;">S</span> {line[2:].strip()}</p>')
        elif line.startswith("W:"):
            html_lines.append(f'<p style="margin:3px 0;font-size:13px;"><span style="background:#fde8d8;padding:1px 5px;border-radius:3px;font-weight:bold;">W</span> {line[2:].strip()}</p>')
        elif line.startswith("O:"):
            html_lines.append(f'<p style="margin:3px 0;font-size:13px;"><span style="background:#d6eaf8;padding:1px 5px;border-radius:3px;font-weight:bold;">O</span> {line[2:].strip()}</p>')
        elif line.startswith("T:"):
            html_lines.append(f'<p style="margin:3px 0;font-size:13px;"><span style="background:#f9ebea;padding:1px 5px;border-radius:3px;font-weight:bold;">T</span> {line[2:].strip()}</p>')
        else:
            key, sep, val = line.partition(":")
            if sep and len(key) <= 6:
                html_lines.append(f'<p style="margin:3px 0;font-size:13px;"><strong>{key}:</strong>{val}</p>')
            else:
                html_lines.append(f'<p style="margin:3px 0;font-size:13px;">{line}</p>')

    return "\n".join(html_lines)


def send_email(report_content):
    sender_email = os.environ["GMAIL_ADDRESS"]
    sender_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient_email = os.environ["RECIPIENT_EMAIL"]
    viewer_url = os.environ.get("VIEWER_URL", "")

    today = date.today().strftime("%Y년 %m월 %d일")
    subject = f"[이수시스템 M&A] {today} 인텔리전스 리포트"

    viewer_link = f'<p style="margin:8px 0;"><a href="{viewer_url}" style="color:#1a5276;">📊 웹에서 전체 리포트 보기 →</a></p>' if viewer_url else ""

    html_body = f"""<html>
<body style="font-family:'Malgun Gothic',Arial,sans-serif;max-width:760px;margin:0 auto;padding:20px;color:#333;font-size:14px;">
<h2 style="color:#1a5276;border-bottom:2px solid #1a5276;padding-bottom:8px;margin-bottom:4px;">이수시스템 M&amp;A 인텔리전스 리포트</h2>
<p style="color:#888;margin:0 0 4px;">{today} | Claude AI 자동 분석</p>
{viewer_link}
<div style="background:#f4f6f8;padding:16px;border-radius:8px;margin:16px 0;line-height:1.8;">
{format_to_html(report_content)}
</div>
<p style="color:#bbb;font-size:11px;">본 리포트는 Claude AI가 자동 생성하였습니다. 투자 결정 전 전문가 검토를 권장합니다.</p>
</body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())

    print(f"[이메일 발송 완료] → {recipient_email}")


def main():
    print("=== 이수시스템 M&A 인텔리전스 에이전트 시작 ===")

    print("\n[1/4] IT 뉴스 크롤링 중...")
    news_list = crawl_news()
    print(f"총 {len(news_list)}건 수집 완료")

    if not news_list:
        print("수집된 뉴스가 없어 종료합니다.")
        return

    print("\n[2/4] Claude AI 분석 중...")
    report = analyze_with_claude(news_list)
    print("분석 완료")
    print(report)  # 로그 확인용

    print("\n[3/4] 리포트 파일 저장 중...")
    save_report(report, news_list)

    print("\n[4/4] 이메일 발송 중...")
    send_email(report)

    print("\n=== 완료 ===")


if __name__ == "__main__":
    main()
