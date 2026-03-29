import os
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from anthropic import Anthropic
from datetime import date

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
    """여러 IT 뉴스 사이트에서 최신 기사 제목을 수집합니다."""
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
    """Claude API로 M&A 관점의 뉴스 분석 및 기업 추천을 수행합니다."""
    news_text = "\n".join(
        [f"- [{item['source']}] {item['title']}" for item in news_list]
    )

    prompt = f"""
당신은 IT 기업 M&A 전문 컨설턴트입니다. 응답은 반드시 아래 형식을 완전히 완성하여 끝까지 작성하세요.
각 항목은 한 문장으로만 작성하고, 절대 중간에 끊지 마세요.

## 의뢰 기업 정보
{ISU_SYSTEM_PROFILE}

## 오늘의 IT 뉴스 목록
{news_text}

## 출력 형식 (반드시 아래 형식 그대로, 끝까지 완성할 것)

=== M&A 핵심 뉴스 TOP 3 ===

[1위] (뉴스 제목)
관련솔루션: (한 단어~짧은 구)
S: (한 문장)
W: (한 문장)
O: (한 문장)
T: (한 문장)
시사점: (한 문장)

[2위] (뉴스 제목)
관련솔루션: (한 단어~짧은 구)
S: (한 문장)
W: (한 문장)
O: (한 문장)
T: (한 문장)
시사점: (한 문장)

[3위] (뉴스 제목)
관련솔루션: (한 단어~짧은 구)
S: (한 문장)
W: (한 문장)
O: (한 문장)
T: (한 문장)
시사점: (한 문장)

=== M&A 유망 기업 추천 (시총 1,000억 이하) ===

[추천1] 기업명 | 업종 | 시총 약 OOO억
역량: (한 문장)
시너지: (한 문장)
S: (한 문장)
W: (한 문장)
O: (한 문장)
T: (한 문장)
주의: (한 문장)

[추천2] 기업명 | 업종 | 시총 약 OOO억
역량: (한 문장)
시너지: (한 문장)
S: (한 문장)
W: (한 문장)
O: (한 문장)
T: (한 문장)
주의: (한 문장)

[추천3] 기업명 | 업종 | 시총 약 OOO억
역량: (한 문장)
시너지: (한 문장)
S: (한 문장)
W: (한 문장)
O: (한 문장)
T: (한 문장)
주의: (한 문장)

=== END ===
"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


def send_email(report_content):
    """Gmail SMTP로 분석 리포트를 발송합니다."""
    sender_email = os.environ["GMAIL_ADDRESS"]
    sender_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient_email = os.environ["RECIPIENT_EMAIL"]

    today = date.today().strftime("%Y년 %m월 %d일")
    subject = f"[이수시스템 M&A 인텔리전스] {today} 아침 IT 동향 리포트"

    def format_to_html(text):
        lines = text.split("\n")
        html_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith("=== ") and line.endswith(" ==="):
                title = line[4:-4]
                html_lines.append(f'<h3 style="color:#fff;background:#1a5276;padding:8px 14px;border-radius:6px;margin-top:24px;margin-bottom:8px;">{title}</h3>')
            elif line.startswith("[1위]") or line.startswith("[2위]") or line.startswith("[3위]"):
                html_lines.append(f'<p style="font-weight:bold;font-size:14px;margin:16px 0 4px;color:#1a5276;">📌 {line}</p>')
            elif line.startswith("[추천1]") or line.startswith("[추천2]") or line.startswith("[추천3]"):
                html_lines.append(f'<p style="font-weight:bold;font-size:14px;margin:16px 0 4px;color:#117a65;">🏢 {line[5:]}</p>')
            elif line.startswith("S:"):
                html_lines.append(f'<p style="margin:3px 0;"><span style="background:#d5f5e3;padding:1px 6px;border-radius:3px;font-weight:bold;font-size:12px;">S 강점</span> {line[2:].strip()}</p>')
            elif line.startswith("W:"):
                html_lines.append(f'<p style="margin:3px 0;"><span style="background:#fde8d8;padding:1px 6px;border-radius:3px;font-weight:bold;font-size:12px;">W 약점</span> {line[2:].strip()}</p>')
            elif line.startswith("O:"):
                html_lines.append(f'<p style="margin:3px 0;"><span style="background:#d6eaf8;padding:1px 6px;border-radius:3px;font-weight:bold;font-size:12px;">O 기회</span> {line[2:].strip()}</p>')
            elif line.startswith("T:"):
                html_lines.append(f'<p style="margin:3px 0;"><span style="background:#f9ebea;padding:1px 6px;border-radius:3px;font-weight:bold;font-size:12px;">T 위협</span> {line[2:].strip()}</p>')
            elif line.startswith("관련솔루션:") or line.startswith("시사점:") or line.startswith("역량:") or line.startswith("시너지:") or line.startswith("주의:"):
                key, _, val = line.partition(":")
                html_lines.append(f'<p style="margin:3px 0;"><strong>{key}:</strong>{val}</p>')
            elif line == "=== END ===":
                html_lines.append('<hr style="border:1px dashed #ccc;margin:16px 0;">')
            elif line == "":
                pass
            else:
                html_lines.append(f'<p style="margin:3px 0;">{line}</p>')
        return "\n".join(html_lines)

    html_body = f"""
<html>
<body style="font-family:'Malgun Gothic',Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#333;font-size:14px;">

<h2 style="color:#1a5276;border-bottom:2px solid #1a5276;padding-bottom:10px;">
    이수시스템 M&amp;A 인텔리전스 리포트
</h2>
<p style="color:#666;">{today} | Claude AI 자동 분석</p>

<div style="background:#f8f9fa;padding:20px;border-radius:8px;margin:20px 0;line-height:1.7;">
{format_to_html(report_content)}
</div>

<hr style="border:1px solid #eee;margin:20px 0;">
<p style="color:#999;font-size:11px;">
    본 리포트는 Claude AI가 자동으로 생성하였습니다. 투자 결정 전 전문가 검토를 권장합니다.
</p>

</body>
</html>
"""

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

    print("\n[1/3] IT 뉴스 크롤링 중...")
    news_list = crawl_news()
    print(f"총 {len(news_list)}건 수집 완료")

    if not news_list:
        print("수집된 뉴스가 없어 종료합니다.")
        return

    print("\n[2/3] Claude AI 분석 중...")
    report = analyze_with_claude(news_list)
    print("분석 완료")

    print("\n[3/3] 이메일 발송 중...")
    send_email(report)

    print("\n=== 완료 ===")


if __name__ == "__main__":
    main()
