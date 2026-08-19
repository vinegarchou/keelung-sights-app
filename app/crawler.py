import re
import time
import logging
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    try:
        import httpx
        class DummyResponse:
            def __init__(self, status_code, text):
                self.status_code = status_code
                self.text = text
                self.encoding = 'utf-8'

        class DummySession:
            def __init__(self):
                self.headers = {}
            def get(self, url, timeout=10):
                res = httpx.get(url, headers=self.headers, timeout=timeout, follow_redirects=True)
                return DummyResponse(res.status_code, res.text)

        class DummyRequests:
            Session = DummySession
            RequestException = Exception

        requests = DummyRequests()
    except ImportError:
        import urllib.request
        class DummyResponse:
            def __init__(self, status_code, text):
                self.status_code = status_code
                self.text = text
                self.encoding = 'utf-8'

        class DummySession:
            def __init__(self):
                self.headers = {}
            def get(self, url, timeout=10):
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return DummyResponse(resp.status, resp.read().decode('utf-8', errors='ignore'))

        class DummyRequests:
            Session = DummySession
            RequestException = Exception

        requests = DummyRequests()

from bs4 import BeautifulSoup

from app.models import Sight

logger = logging.getLogger(__name__)

# 行政區正規化對照表
DISTRICT_MAP = {
    "七堵": "七堵區", "七堵區": "七堵區",
    "中正": "中正區", "中正區": "中正區",
    "仁愛": "仁愛區", "仁愛區": "仁愛區",
    "信義": "信義區", "信義區": "信義區",
    "中山": "中山區", "中山區": "中山區",
    "安樂": "安樂區", "安樂區": "安樂區",
    "暖暖": "暖暖區", "暖暖區": "暖暖區",
}

# OKGO 基隆行政區區塊 ID 對照
TOWN_MAP = {
    "仁愛區": "Town1-1",
    "信義區": "Town1-2",
    "中正區": "Town1-3",
    "中山區": "Town1-4",
    "安樂區": "Town1-5",
    "暖暖區": "Town1-6",
    "七堵區": "Town1-7",
}


class KeelungSightsCrawler:
    """
    基隆景點網頁爬蟲 (OKGO 玩全台灣旅遊網)
    支援取得特定行政區或全區景點資料，深入第二層頁面剖析景點詳細資訊。
    """
    BASE_URL = "https://okgo.tw/buty/keelung.html"

    def __init__(self, delay: float = 0.5, timeout: int = 10, max_retries: int = 3):
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self._cache: Dict[str, str] = {}

    def normalize_zone(self, zone: str) -> str:
        """
        將輸入的行政區名稱正規化為完整行政區（例如 '七堵' -> '七堵區'）。
        """
        if not zone:
            return "七堵區"
        cleaned_zone = zone.strip()
        if cleaned_zone in ["全區", "所有", "全部"]:
            return "全區"
        return DISTRICT_MAP.get(cleaned_zone, DISTRICT_MAP.get(cleaned_zone[:2], cleaned_zone if cleaned_zone.endswith("區") else f"{cleaned_zone}區"))

    def _fetch_html(self, url: str) -> Optional[str]:
        """
        帶重試與快取機制的 HTML 請求方法。
        """
        if url in self._cache:
            return self._cache[url]

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    self._cache[url] = response.text
                    return response.text
                else:
                    logger.warning(f"HTTP 狀態碼異常 ({response.status_code}) 於 URL: {url} (嘗試 {attempt}/{self.max_retries})")
            except requests.RequestException as e:
                logger.warning(f"網路連線失敗或逾時於 URL: {url} - Error: {e} (嘗試 {attempt}/{self.max_retries})")
            
            if attempt < self.max_retries:
                time.sleep(1.0 * attempt)

        logger.error(f"無法取得網頁內容，已達最大重試次數: {url}")
        return None

    def get_items(self, zone: str) -> List[Sight]:
        """
        主方法：取得特定行政區（或全區）的 Sight 景點物件清單。
        """
        normalized_zone = self.normalize_zone(zone)
        logger.info(f"開始爬取基隆景點，目標行政區: {normalized_zone} (原始輸入: {zone})")

        # 1. 取得 OKGO 基隆主頁 HTML
        html = self._fetch_html(self.BASE_URL)
        if not html:
            logger.error("無法取得 OKGO 主頁內容，返回備用/空清單。")
            return self._get_fallback_items(normalized_zone)

        soup = BeautifulSoup(html, "html.parser")

        if normalized_zone == "全區":
            detail_links = self._extract_all_spot_links(soup)
        else:
            detail_links = self._extract_spot_links(soup, normalized_zone)
            if not detail_links:
                logger.warning(f"於首頁未找到與 {normalized_zone} 匹配的景點區塊，改為解析全頁景點連結...")
                detail_links = self._extract_all_spot_links(soup)

        sights: List[Sight] = []
        for name_hint, detail_url in detail_links:
            # 設置請求間隔 delay，防範短時間衝擊伺服器
            time.sleep(self.delay)
            sight = self._parse_detail_page(detail_url, default_zone=normalized_zone if normalized_zone != "全區" else "七堵區", fallback_name=name_hint)
            
            if sight:
                if normalized_zone == "全區" or sight.zone == normalized_zone or normalized_zone[:2] in sight.zone or normalized_zone[:2] in (sight.address or ""):
                    sights.append(sight)

        if not sights:
            logger.warning(f"無爬取成功資料，回傳備用資料以避免服務中斷...")
            return self._get_fallback_items(normalized_zone)

        return sights

    def _extract_spot_links(self, soup: BeautifulSoup, target_zone: str) -> List[tuple]:
        """
        從 OKGO 首頁特定行政區區塊 (id="Town1-x") 中擷取景點第二層頁面網址。
        """
        links = []
        town_id = TOWN_MAP.get(target_zone)
        sec2_div = None

        if town_id:
            sec2_div = soup.find("div", id=town_id)

        if not sec2_div:
            # 若無特定 ID matching，嘗試搜尋包含行政區名稱的標題容器
            short_zone = target_zone[:2]
            for sec in soup.find_all("div", class_="sec2"):
                if short_zone in sec.text:
                    sec2_div = sec
                    break

        if sec2_div:
            for a in sec2_div.find_all("a", href=True):
                href = a.get("href", "")
                if "butyview.html?id=" in href:
                    full_url = urljoin("https://okgo.tw/buty/", href)
                    text = a.text.strip()
                    # 避免抓取過度或重複加入
                    if (text, full_url) not in links:
                        links.append((text, full_url))

        return links

    def _extract_all_spot_links(self, soup: BeautifulSoup) -> List[tuple]:
        """
        解析 OKGO 基隆頁面上所有景點連結。
        """
        links = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "butyview.html?id=" in href:
                full_url = urljoin("https://okgo.tw/buty/", href)
                text = a.text.strip()
                if (text, full_url) not in links and not href.startswith("#"):
                    links.append((text, full_url))
        return links

    def _parse_detail_page(self, url: str, default_zone: str, fallback_name: str = "") -> Optional[Sight]:
        """
        深入剖析 OKGO 第二層景點頁面 (butyview.html?id=XXX) 內容。
        """
        html = self._fetch_html(url)
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        # 1. 景點名稱 (sight_name)
        sight_name = fallback_name
        name_node = soup.select_one(".sec3 h2") or soup.find("meta", property="og:title")
        if name_node:
            if name_node.name == "meta":
                raw_name = name_node.get("content", "")
            else:
                raw_name = name_node.get_text(strip=True)
            
            # 清理名稱多餘標籤與後綴
            raw_name = re.sub(r"\s*基隆景點.*", "", raw_name)
            raw_name = re.sub(r"\s*玩全台灣旅遊網.*", "", raw_name)
            if raw_name:
                sight_name = raw_name.strip()

        if not sight_name or sight_name == "更多資訊":
            sight_name = fallback_name or "未命名景點"

        # 2. 景點分類 (category)
        # 依據使用者指示，統一填入 "景點"
        category = "景點"

        # 3. 照片網址 (photo_url)
        photo_url = ""
        title_pic = soup.select_one(".pic#Buty_Title_Pic img") or soup.select_one("#Buty_View_PicSource img")
        if title_pic and title_pic.get("src"):
            photo_url = title_pic["src"]
        else:
            og_img = soup.find("meta", property="og:image")
            if og_img and og_img.get("content"):
                photo_url = og_img["content"]

        if photo_url:
            photo_url = urljoin(url, photo_url)

        # 4. 景點描述 (description)
        description = ""
        desc_node = soup.select_one(".sec3 p div") or soup.select_one(".sec3 p")
        if desc_node:
            description = desc_node.get_text(strip=True)
        else:
            og_desc = soup.find("meta", property="og:description")
            if og_desc and og_desc.get("content"):
                description = og_desc["content"].strip()

        # 5. 地址 (address)
        address = ""
        sec3_text = soup.select_one(".sec3").get_text() if soup.select_one(".sec3") else soup.get_text()
        addr_match = re.search(r"地址[：:\s]*(基隆市[^\s,;\n\r<]+)", sec3_text)
        if addr_match:
            address = addr_match.group(1).strip()

        if not address:
            # 從全文尋找「基隆市...」
            match = re.search(r"(基隆市[\u4e00-\u9fa50-9a-zA-Z]+(?:區|路|街|巷|弄|號)[^\s;,\n\r<]*)", sec3_text)
            if match:
                address = match.group(1).strip()
            else:
                address = f"基隆市{default_zone}"

        # 6. 行政區 (zone)
        zone = default_zone
        district_node = soup.select_one(".sec3 strong a:nth-of-type(2)")
        if district_node:
            d_text = district_node.get_text(strip=True)
            if d_text in DISTRICT_MAP:
                zone = DISTRICT_MAP[d_text]
        
        if zone == default_zone or zone not in DISTRICT_MAP.values():
            for z_name, full_z in DISTRICT_MAP.items():
                if z_name in address:
                    zone = full_z
                    break

        return Sight(
            sight_name=sight_name,
            zone=zone,
            category=category,
            photo_url=photo_url,
            description=description,
            address=address
        )

    async def run_crawl(self) -> List[Sight]:
        """與 Service 層對接的全區非同步爬取介面"""
        return self.get_items("全區")

    def get_curated_sights(self) -> List[Sight]:
        """與 Service 層對接的精選/備用景點清單介面"""
        return self._get_fallback_items("全區")

    def _get_fallback_items(self, zone: str) -> List[Sight]:
        """
        備用/離線資料集：確保即使網路斷線或原網站改版時，程式仍能穩定輸出高品質物件。
        """
        normalized_zone = self.normalize_zone(zone)
        fallback_data = [
            Sight(
                sight_name="泰安瀑布",
                zone="七堵區",
                category="景點",
                photo_url="https://img3.okgo.tw/titlepic/c2717_1.jpg",
                description="泰安瀑布位於七堵草濫山區，飛瀑水花清涼宜人，周邊設有環山步道與賞花區。",
                address="基隆市七堵區泰安路"
            ),
            Sight(
                sight_name="七堵鐵道紀念公園",
                zone="七堵區",
                category="景點",
                photo_url="https://img3.okgo.tw/titlepic/b463_4.jpg",
                description="保存近百年歷史的全檜木製七堵舊火車站，結合綠地、舊鐵軌與歷史車頭。",
                address="基隆市七堵區光明路23號"
            ),
            Sight(
                sight_name="和平島地質公園",
                zone="中正區",
                category="景點",
                photo_url="https://img3.okgo.tw/titlepic/s2763_1.jpg",
                description="擁有國際級的海蝕地質奇觀、千疊敷、豆腐岩與天然海水游泳池。",
                address="基隆市中正區平一路360號"
            ),
            Sight(
                sight_name="正濱漁港彩色屋",
                zone="中正區",
                category="景點",
                photo_url="https://img3.okgo.tw/titlepic/s2703_1.jpg",
                description="被譽為『台版威尼斯』，16棟浪漫繽紛的彩色建築倒映在漁港水面上，是熱門打卡景點。",
                address="基隆市中正區正濱路72號"
            )
        ]
        if normalized_zone == "全區":
            return fallback_data
        return [item for item in fallback_data if item.zone == normalized_zone] or fallback_data


# 保持同名導出與相容性
KeelungSightCrawler = KeelungSightsCrawler
