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
이수시스템(ISU SYSTEM)의 사업 영역 (우선순위 순서):

★ 주력사업 (최우선):
- HR: Smart HR, WORKUP, HR-Tong (500개 이상 기업 구축 경험) — 핵심 매출원

▶ 주요사업:
- AI: 챗봇, HR AI Package, AI 플랫폼, AI 이력서 분석
- 디지털 서비스: ERP 솔루션, RPA, Smart Root
- ESG: ESG 데이터 플랫폼 (지표관리, 공급망관리)

▶ 부가사업:
- 안전: Smart Plant, Smart & Safety, BizPTT (산업현장 안전관리)
- 클라우드 인프라: Cloud Platform

현재 M&A를 통해 사업 시너지를 낼 수 있는 기업을 탐색 중입니다.
뉴스 및 M&A 기업 추천 시 HR 관련 연관성을 최우선으로 평가하세요.
"""

BIRTH_INFO = {
    "date": "1983년 9월 4일",
    "time": "22시 55분 (해시/亥時)",
    "place": "충청남도 강경",
    "solar_date": "1983-09-04"
}

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


def analyze_with_claude(news_list, today_str):
    # 뉴스 목록 (URL 포함)
    news_text = "\n".join(
        [f"[{i+1}] [{item['source']}] {item['title']}\n    URL: {item['url']}" for i, item in enumerate(news_list)]
    )

    system = "당신은 사주명리학 전문가이자 IT 기업 M&A 컨설턴트입니다. 주어진 형식을 반드시 끝까지 완성하고 === END ===로 마무리하세요."

    prompt = f"""오늘 날짜: {today_str}

## [파트1] 사주 일일 운세
생년월일시: {BIRTH_INFO['date']} {BIRTH_INFO['time']} ({BIRTH_INFO['place']} 출생)

위 사주를 분석하여 아래 형식으로 작성하세요. 각 항목은 2문장 이내로 작성하세요.

[사주기반운세]
성경구절: (오늘 사주 흐름과 어울리는 성경 구절 1개, 장절 포함)
성경해석: (해당 구절이 오늘 사주와 어떻게 연결되는지 한 문장)
오늘의기운: (오늘 사주의 전반적인 기운 한 문장)
좋은것: (오늘 특히 좋은 것 또는 유리한 상황 한 문장)
조심할것: (오늘 조심해야 할 것 한 문장)
행운의방향: (오늘 행운의 방위나 색상 등 간단히)

## [파트2] M&A 인텔리전스
의뢰기업: {ISU_SYSTEM_PROFILE}

수집된 뉴스 목록 (번호와 URL 주목):
{news_text}

위 뉴스 중 M&A 전략에 가장 중요한 3건을 선별하고,
반드시 위 목록에 있는 실제 URL을 그대로 복사하여 매핑하세요 (URL 절대 수정/창작 금지).

[뉴스1] 뉴스제목
관련솔루션:
S:
W:
O:
T:
시사점:
URL: (위 목록에서 해당 뉴스의 URL 그대로)

[뉴스2] 뉴스제목
관련솔루션:
S:
W:
O:
T:
시사점:
URL: (위 목록에서 해당 뉴스의 URL 그대로)

[뉴스3] 뉴스제목
관련솔루션:
S:
W:
O:
T:
시사점:
URL: (위 목록에서 해당 뉴스의 URL 그대로)

시총 1,000억원 이하 M&A 유망 기업 3곳을 추천하세요.
기업 홈페이지 URL은 실제로 존재할 가능성이 높은 것만 작성하고, 확실하지 않으면 검색URL로 대체하세요.

[기업1] 기업명 | 업종 | 시총약OOO억
역량:
시너지:
S:
W:
O:
T:
주의:
홈페이지: (실제 홈페이지 URL 또는 https://www.google.com/search?q=기업명)

[기업2] 기업명 | 업종 | 시총약OOO억
역량:
시너지:
S:
W:
O:
T:
주의:
홈페이지: (실제 홈페이지 URL 또는 https://www.google.com/search?q=기업명)

[기업3] 기업명 | 업종 | 시총약OOO억
역량:
시너지:
S:
W:
O:
T:
주의:
홈페이지: (실제 홈페이지 URL 또는 https://www.google.com/search?q=기업명)

=== END ==="""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=6000,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text


def save_report(report_content, news_list, today_str):
    os.makedirs("reports", exist_ok=True)
    data = {
        "date": today_str,
        "generated_at": datetime.now().isoformat(),
        "news_count": len(news_list),
        "content": report_content
    }
    with open(f"reports/{today_str}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    index_path = "reports/index.json"
    index = []
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    if today_str not in index:
        index.insert(0, today_str)
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False)
    print(f"[리포트 저장] reports/{today_str}.json")


def parse_section(content, start_tag, end_tag=None):
    """content에서 start_tag ~ end_tag 사이 내용 추출"""
    lines = content.split("\n")
    result = []
    in_section = False
    for line in lines:
        if start_tag in line:
            in_section = True
            continue
        if in_section:
            if end_tag and end_tag in line:
                break
            if line.strip().startswith("[뉴스") or line.strip().startswith("[기업") or line.strip() == "=== END ===":
                if start_tag not in ("[사주기반운세]",):
                    break
            result.append(line)
    return "\n".join(result).strip()


def build_email_html(report_content, today_str, viewer_url):
    lines = report_content.split("\n")

    # 파싱
    saju = {}
    news_items = []
    company_items = []
    current = None
    mode = None

    for line in lines:
        s = line.strip()
        if s == "[사주기반운세]":
            mode = "saju"
            continue
        if s.startswith("[뉴스"):
            if current and mode == "news": news_items.append(current)
            if current and mode == "company": company_items.append(current)
            current = {"header": s[6:].strip(), "fields": {}}
            mode = "news"
            continue
        if s.startswith("[기업"):
            if current and mode == "news": news_items.append(current)
            if current and mode == "company": company_items.append(current)
            current = {"header": s[5:].strip(), "fields": {}}
            mode = "company"
            continue
        if s == "=== END ===":
            if current and mode == "news": news_items.append(current)
            if current and mode == "company": company_items.append(current)
            break

        if ":" in s:
            key, _, val = s.partition(":")
            val = val.strip()
            if mode == "saju":
                saju[key.strip()] = val
            elif mode in ("news", "company") and current:
                current["fields"][key.strip()] = val

    # 사주 섹션 HTML
    saju_html = f"""
<div style="background:linear-gradient(135deg,#1a3a5c,#2471a3);color:#fff;border-radius:10px;padding:18px 20px;margin-bottom:16px;">
  <div style="font-size:15px;font-weight:bold;margin-bottom:12px;">✝️ 오늘의 말씀 & 사주 운세</div>
  <div style="background:rgba(255,255,255,.1);border-radius:8px;padding:12px;margin-bottom:10px;font-style:italic;">
    &ldquo;{saju.get('성경구절','')}&rdquo;<br>
    <span style="font-size:12px;opacity:.85;">{saju.get('성경해석','')}</span>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <tr><td style="padding:4px 8px;opacity:.8;white-space:nowrap;">오늘의 기운</td><td style="padding:4px 8px;">{saju.get('오늘의기운','')}</td></tr>
    <tr><td style="padding:4px 8px;color:#7dcea0;white-space:nowrap;">✅ 좋은 것</td><td style="padding:4px 8px;">{saju.get('좋은것','')}</td></tr>
    <tr><td style="padding:4px 8px;color:#f1948a;white-space:nowrap;">⚠️ 조심할 것</td><td style="padding:4px 8px;">{saju.get('조심할것','')}</td></tr>
    <tr><td style="padding:4px 8px;opacity:.8;white-space:nowrap;">🍀 행운</td><td style="padding:4px 8px;">{saju.get('행운의방향','')}</td></tr>
  </table>
</div>"""

    # 뉴스 헤드라인만
    news_rows = ""
    for i, n in enumerate(news_items[:3], 1):
        url = n["fields"].get("URL", "")
        title = n["header"]
        tip = n["fields"].get("시사점", "")
        link = f'<a href="{url}" style="color:#1a5276;text-decoration:none;" target="_blank">{title}</a>' if url else title
        news_rows += f"""
<tr>
  <td style="padding:8px 6px;border-bottom:1px solid #eee;font-size:13px;vertical-align:top;">
    <span style="background:#1a5276;color:#fff;border-radius:3px;padding:1px 6px;font-size:11px;margin-right:6px;">{i}위</span>{link}<br>
    <span style="color:#888;font-size:12px;margin-left:32px;">{tip}</span>
  </td>
</tr>"""

    # 기업 헤드라인만
    company_rows = ""
    for i, c in enumerate(company_items[:3], 1):
        url = c["fields"].get("홈페이지", "")
        name = c["header"]
        synergy = c["fields"].get("시너지", "")
        link = f'<a href="{url}" style="color:#117a65;text-decoration:none;" target="_blank">{name}</a>' if url else name
        company_rows += f"""
<tr>
  <td style="padding:8px 6px;border-bottom:1px solid #eee;font-size:13px;vertical-align:top;">
    <span style="background:#117a65;color:#fff;border-radius:3px;padding:1px 6px;font-size:11px;margin-right:6px;">{i}</span>{link}<br>
    <span style="color:#888;font-size:12px;margin-left:32px;">{synergy}</span>
  </td>
</tr>"""

    viewer_btn = f'<a href="{viewer_url}" style="display:inline-block;background:#1a5276;color:#fff;padding:10px 20px;border-radius:6px;text-decoration:none;font-size:13px;">📊 전체 리포트 보기 →</a>' if viewer_url else ""

    today_kr = datetime.strptime(today_str, "%Y-%m-%d").strftime("%Y년 %m월 %d일")

    return f"""<html>
<body style="font-family:'Malgun Gothic',Arial,sans-serif;max-width:620px;margin:0 auto;padding:20px;color:#333;font-size:14px;">

<h2 style="color:#1a5276;border-bottom:2px solid #1a5276;padding-bottom:8px;margin-bottom:4px;">이수시스템 M&amp;A 인텔리전스</h2>
<p style="color:#999;font-size:12px;margin:0 0 16px;">{today_kr} | Claude AI 자동 분석</p>

{saju_html}

<div style="margin-bottom:16px;">
  <div style="background:#1a5276;color:#fff;padding:7px 14px;border-radius:6px 6px 0 0;font-size:13px;font-weight:bold;">📰 M&amp;A 핵심 뉴스 TOP 3</div>
  <table style="width:100%;border-collapse:collapse;border:1px solid #eee;border-top:none;border-radius:0 0 6px 6px;">
    {news_rows}
  </table>
</div>

<div style="margin-bottom:16px;">
  <div style="background:#117a65;color:#fff;padding:7px 14px;border-radius:6px 6px 0 0;font-size:13px;font-weight:bold;">🏢 M&amp;A 유망 기업 추천 (시총 1,000억 이하)</div>
  <table style="width:100%;border-collapse:collapse;border:1px solid #eee;border-top:none;border-radius:0 0 6px 6px;">
    {company_rows}
  </table>
</div>

<div style="text-align:center;margin:20px 0;">
  {viewer_btn}
</div>

<p style="color:#ccc;font-size:11px;text-align:center;">본 리포트는 Claude AI가 자동 생성하였습니다. 투자 결정 전 전문가 검토를 권장합니다.</p>
</body></html>"""


def send_email(report_content, today_str):
    sender_email = os.environ["GMAIL_ADDRESS"]
    sender_password = os.environ["GMAIL_APP_PASSWORD"]
    recipient_email = os.environ["RECIPIENT_EMAIL"]
    viewer_url = os.environ.get("VIEWER_URL", "")

    today_kr = datetime.strptime(today_str, "%Y-%m-%d").strftime("%Y년 %m월 %d일")
    subject = f"[이수시스템 M&A] {today_kr} 인텔리전스 + 오늘의 운세"

    html_body = build_email_html(report_content, today_str, viewer_url)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())

    print(f"[이메일 발송 완료] → {recipient_email}")


def load_existing_report(today_str):
    """오늘 이미 생성된 리포트가 있으면 불러옵니다."""
    path = f"reports/{today_str}.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("content")
    return None


def main():
    print("=== 이수시스템 M&A 인텔리전스 에이전트 시작 ===")
    today_str = date.today().isoformat()

    # 오늘 이미 분석한 결과가 있으면 재사용 (순서/내용 고정)
    existing = load_existing_report(today_str)
    if existing:
        print(f"\n[캐시] {today_str} 리포트가 이미 존재합니다. 저장된 결과를 사용합니다.")
        report = existing
    else:
        print("\n[1/4] IT 뉴스 크롤링 중...")
        news_list = crawl_news()
        print(f"총 {len(news_list)}건 수집 완료")

        if not news_list:
            print("수집된 뉴스가 없어 종료합니다.")
            return

        print("\n[2/4] Claude AI 분석 중...")
        report = analyze_with_claude(news_list, today_str)
        print("분석 완료\n")
        print(report)

        print("\n[3/4] 리포트 파일 저장 중...")
        save_report(report, news_list, today_str)

    print("\n[4/4] 이메일 발송 중...")
    send_email(report, today_str)

    print("\n=== 완료 ===")


if __name__ == "__main__":
    main()
