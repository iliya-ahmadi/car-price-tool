import re
import statistics
from urllib.parse import quote_plus

import requests
import streamlit as st
from bs4 import BeautifulSoup

st.markdown("""
<style>

/* دکمه submit داخل فرم */
div[data-testid="stFormSubmitButton"] > button {
    background-color: #22c55e !important;
    color: white !important;
    border-radius: 10px !important;
    height: 48px !important;
    font-size: 16px !important;
    border: none !important;
}

div[data-testid="stFormSubmitButton"] > button:hover {
    background-color: #16a34a !important;
    color: white !important;
}

</style>
""", unsafe_allow_html=True)


st.set_page_config(page_title="Car Price Tool", layout="centered")  # یا wide اگر خواستی
st.markdown("""
<style>
/* از همون اول صفحه رو جمع‌وجور کن */
.block-container{
    max-width: 900px;
    padding-top: 2rem;
}

/* ورودی‌ها و فرم خیلی پخش نشه */
div[data-testid="stForm"]{
    max-width: 900px;
    margin: 0 auto;
}
</style>
""", unsafe_allow_html=True)

def build_url(city: str, query: str) -> str:
    encoded_query = quote_plus(query)
    return f"https://divar.ir/s/{city}?q={encoded_query}"

def fmt_price(price: int) -> str:
    million = price / 1_000_000
    return f"{million:,.0f} میلیون تومان"

def fmt_compact_toman(price: int) -> tuple[str, str]:
    """
    خروجی: (عدد، واحد)
    مثال:
    1_520_000_000 -> ("1.52", "میلیارد تومان")
    520_000_000   -> ("520", "میلیون تومان")
    """
    if price >= 1_000_000_000:
        val = price / 1_000_000_000
        return (f"{val:.2f}", "میلیارد تومان")
    else:
        val = price / 1_000_000
        return (f"{val:.0f}", "میلیون تومان")
    
    
def metric_card(title: str, price: int):
    val, unit = fmt_compact_toman(price)
    st.markdown(f"""
    <div style="
        background:#ffffff;
        border:1px solid rgba(0,0,0,0.06);
        border-radius:18px;
        padding:16px 14px;
        box-shadow:0 8px 22px rgba(0,0,0,0.04);
        height:110px;
    ">
        <div style="font-size:14px; color:rgba(0,0,0,0.55); margin-bottom:8px;">{title}</div>
        <div style="font-size:34px; font-weight:800; line-height:1;">{val}</div>
        <div style="font-size:14px; color:rgba(0,0,0,0.60); margin-top:6px;">{unit}</div>
    </div>
    """, unsafe_allow_html=True)

def fetch_page(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text


def fa_to_en_digits(s: str) -> str:
    trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return s.translate(trans)


def extract_prices(html: str) -> list[int]:
    soup = BeautifulSoup(html, "html.parser")
    prices: list[int] = []

    for text_node in soup.find_all(string=lambda t: t and "تومان" in t):
        text = fa_to_en_digits(text_node.strip())

        if "توافقی" in text:
            continue

        text = text.replace("٬", ",")
        nums = re.findall(r"\d[\d,]*", text)
        if not nums:
            continue

        candidate = max(nums, key=len).replace(",", "")
        try:
            price = int(candidate)
        except ValueError:
            continue

        if 1_000_000 <= price <= 50_000_000_000:
            prices.append(price)

    return prices


def remove_outliers_iqr(prices: list[int]) -> list[int]:
    if len(prices) < 8:
        return prices

    s = sorted(prices)
    n = len(s)

    def percentile(p: float) -> float:
        idx = (n - 1) * p
        lo = int(idx)
        hi = min(lo + 1, n - 1)
        frac = idx - lo
        return s[lo] * (1 - frac) + s[hi] * frac

    q1 = percentile(0.25)
    q3 = percentile(0.75)
    iqr = q3 - q1

    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr

    return [x for x in prices if low <= x <= high]


def fmt_toman(x: int) -> str:
    return f"{x:,} تومان"

def normalize_year(year: str) -> str:
    
   def normalize_year(year) -> str:
    year = "" if year is None else str(year)   # تبدیل به رشته
    year = year.strip()
    year = fa_to_en_digits(year)

    if not year:
        return ""
    # ادامه‌ی کدت...

    # فقط رقم‌ها
    year = "".join(ch for ch in year if ch.isdigit())

    if len(year) == 4 and year.startswith("13"):
        return year[2:]  # 1394 -> 94

    if len(year) == 2:
        return year

    # اگر چیز عجیب وارد شد، بی‌خیال می‌شیم
    return ""


def build_query(car_name: str, year: str) -> str:
    car_name = (car_name or "").strip()
    y = normalize_year(year)
    if y:
        return f"{car_name} مدل {y}"
    return car_name
# ------------------ UI ------------------

st.set_page_config(page_title="Car Price Tool", page_icon="🚗", layout="centered")
st.title("🚗 Car Price Tool (Divar)")

import streamlit as st

st.set_page_config(page_title="تحلیل قیمت خودرو", page_icon="🚗", layout="wide")

st.markdown("""
    <style>
    /* کارت کلی فرم */
    .input-card {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 16px;
    padding: 18px 18px 10px 18px;
    }

    /* عنوان بخش */
    .section-title {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 10px;
    }

    /* متن‌های ریز زیر ورودی */
    .hint {
    opacity: 0.75;
    font-size: 12px;
    margin-top: -6px;
    }

    /* دکمه اصلی */
    .stButton>button {
    width: 100%;
    border-radius: 12px;
    padding: 10px 12px;
    font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)


with st.form("search_form"):
    st.markdown("### مشخصات خودرو")
    st.divider()

    col1, col2, col3 = st.columns([1.5,1,1])

    with col1:
        car_name = st.text_input(
            "نام خودرو",
            placeholder="مثلاً: 206 تیپ 2"
        )

    with col2:
        year = st.number_input(
            "سال ساخت",
            min_value=1380,
            max_value=1405,
            value=1394,
            step=1
        )

    with col3:
        CITY_MAP = {
            "تهران": "tehran",
            "مشهد": "mashhad",
            "اصفهان": "isfahan",
            "اردبیل":"ardabil",
            "شیراز": "shiraz",
            "تبریز": "tabriz",
            "کرج": "karaj",
            "اهواز": "ahvaz",
            "قم": "qom",
            "رشت": "rasht",
            "کرمان": "kerman",
            "یزد": "yazd",
            "زاهدان": "zahedan",
            "ارومیه": "urmia",
            "کرمانشاه": "kermanshah",
            "همدان": "hamedan",
            "قزوین": "qazvin",
            "اراک": "arak",
            "ساری": "sari",
            "گرگان": "gorgan",
            "بندرعباس": "bandarabbas",
        }
        
        city_fa = st.selectbox(
        "شهر",
        options=list(CITY_MAP.keys()),
        index=0
         )
        
        city = CITY_MAP[city_fa]

    use_outlier_filter = st.checkbox(
        "حذف قیمت‌های پرت (پیشنهادی)",
        value=True
    )

    btn = st.form_submit_button(
        "تحلیل قیمت",
        use_container_width=True
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

if btn:

    if not car_name:
        st.error("لطفاً نام خودرو را وارد کن.")
        st.stop()

    car_query = build_query(car_name, year)

    url = build_url(city, car_query)
    # st.caption(f"لینک جستجو: {url}")

    try:
        with st.spinner("در حال دریافت اطلاعات از دیوار..."):
            html = fetch_page(url)
            prices = extract_prices(html)

        # st.write(f"تعداد قیمت‌های استخراج‌شده: {len(prices)}")

        if not prices:
            st.warning("قیمتی پیدا نشد. عبارت را ساده‌تر کن یا شهر را تغییر بده.")
            st.stop()

        raw_count = len(prices)
        
        if use_outlier_filter:
            prices = remove_outliers_iqr(prices)

        # st.write(f"تعداد بعد از فیلتر: {len(prices)} (از {raw_count})")

        final_count = len(prices)
        
        if not prices:
            st.warning("بعد از فیلتر، داده‌ای باقی نماند.")
            st.stop()

        st.markdown("</div>", unsafe_allow_html=True)
        
        min_price = min(prices)
        max_price = max(prices)
        avg_price = int(statistics.mean(prices))
        median_price = int(statistics.median(prices))

        st.subheader("نتیجه تحلیل بازار")

        c1, c2, c3, c4 = st.columns(4)
        with c1: metric_card("کمترین قیمت", min_price)
        with c2: metric_card("بیشترین قیمت", max_price)
        with c3: metric_card("میانگین قیمت", avg_price)
        with c4: metric_card("میانه بازار", median_price)

        st.divider()
        # st.caption("نمونه قیمت‌های استفاده‌شده (۱۰ مورد اول):")
        # st.write([fmt_toman(x) for x in sorted(prices)[:10]])

    except requests.HTTPError as e:
        st.error(f"خطای HTTP: {e}")
    except requests.RequestException as e:
        st.error(f"مشکل شبکه/درخواست: {e}")
    except Exception as e:
        st.error(f"خطای غیرمنتظره: {e}")