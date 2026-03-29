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
당신은 IT 기업 M&A 전문 컨설턴트입니다.

## 의뢰 기업 정보
{ISU_SYSTEM_PROFILE}

## 오늘의 IT 뉴스 목록
{news_text}

## 요청 사항

### 1. M&A 관련 주목 뉴스 (최대 5건)
위 뉴스 중 이수시스템의 M&A 전략과 시너지가 날 수 있는 뉴스를 선별하여 아래 형식으로 작성하세요:

**뉴스 제목**
- 관련 솔루션: (이수시스템의 어떤 솔루션과 연관되는지)
- SWOT 한줄: (Strength/Weakness/Opportunity/Threat 중 핵심 1가지 관점으로 한 문장)
- 시사점: (M&A 전략에서 어떻게 활용할 수 있는지 2-3문장)

### 2. 오늘의 M&A 유망 한국 기업 추천 (3건)
뉴스 트렌드를 바탕으로 이수시스템이 인수하면 시너지가 날 수 있는 한국 IT 기업을 추천하세요:

**기업명** (업종/규모 추정)
- 보유 역량:
- 시너지 포인트:
- SWOT 한줄:
- 주의사항:

응답은 한국어로, 실무자가 바로 활용할 수 있도록 명확하고 간결하게 작성해주세요.
"""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=3000,
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

    html_body = f"""
<html>
<body style="font-family: 'Malgun Gothic', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #333;">

<h2 style="color: #1a5276; border-bottom: 2px solid #1a5276; padding-bottom: 10px;">
    📊 이수시스템 M&A 인텔리전스 리포트
</h2>
<p style="color: #666;">{today} | AI 기반 자동 분석</p>

<div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
{report_content.replace(chr(10), '<br>').replace('**', '<strong>').replace('**', '</strong>')}
</div>

<hr style="border: 1px solid #eee; margin: 20px 0;">
<p style="color: #999; font-size: 12px;">
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
