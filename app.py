import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- MUST BE FIRST --- 網頁基本設定 (包含新 Emoji) ---
st.set_page_config(page_title="🌸 家居單據智能分析 🎀", page_icon="🧾", layout="centered", initial_sidebar_state="collapsed")

# --- CSS 魔法時間 (自定義日系 UI 樣式) ---
# 主色調: 櫻花粉 (#FFC0CB), 文字深灰 (#4F4F4F), 卡片白 (#FFFFFF), 掣醒目粉 (#FF80AB)
custom_css = """
<style>
    /* 覆蓋整個背景顏色為乾淨的白米色，偏軟性 */
    .stApp {
        color: #4F4F4F;
        background-color: #FDF9F9;
    }

    /* 隱藏最頂灰色 Header ( Hamburger Menu, Github Icon) 和 Footer */
    header {visibility: hidden;}
    #stDecoration {display:none;}
    .appview-container .main header {display:none;}
    
    /* 標題和文字字體 */
    h1, h2, h3, p {
        color: #4F4F4F;
        font-family: 'Helvetica Neue', 'Segoe UI', serif;
    }

    /* 上傳圖片區域 */
    div[data-testid="stFileUploadDropzone"] {
        border: 2px dashed #FFC0CB !important; /* 柔和粉紅虛線 */
        background-color: #FFFFFF;
        border-radius: 15px;
    }
    div[data-testid="stFileUploadDropzone"] div {
        color: #4F4F4F !important;
    }

    /* 已準備單據的小圖片卡片 */
    [data-testid="stImage"] {
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(255, 192, 203, 0.3); /* 淡淡粉紅陰影 */
    }

    /* --- THE BIG BUTTON (開始分析個掣) --- */
    /* 讓它更容易睇、更女性化 */
    div.stButton {
        display: flex;
        justify-content: center; /* 居中 */
        margin-top: 1.5rem;
    }

    div.stButton > button {
        background-color: #FF80AB !important; /* 鮮艷粉紅 */
        color: white !important;
        border-radius: 30px !important; /* Kawaii 圓角 */
        border: none !important;
        padding: 1rem 3.5rem !important; /* 加大 padding */
        font-size: 1.3rem !important; /* 字體加大 */
        font-weight: bold !important;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(255, 128, 171, 0.4); /* 淡淡陰影 */
    }

    /* Hover effect */
    div.stButton > button:hover {
        background-color: #FF5280 !important; /* Slightly darker pink */
        transform: translateY(-2px); /* Slight lift */
    }
    
    /* Active (click) effect */
    div.stButton > button:active {
        transform: translateY(1px); /* Slight press */
    }

    /* 輸出報告結果文字區 */
    div[data-testid="stMarkdownContainer"] pre code {
        border-radius: 10px;
        padding: 10px;
    }

    /* 樣式化成功/警告框 */
    div[data-testid="stInfo"] {background-color: #FDF2F2; color: #4F4F4F; border: 1px solid #FFC0CB; border-radius: 10px;}
    div[data-testid="stSuccess"] {background-color: #E8F5E9; color: #1B5E20; border: 1px solid #C8E6C9; border-radius: 10px;}
    div[data-testid="stError"] {background-color: #FFEBEE; color: #B71C1C; border: 1px solid #FFCDD2; border-radius: 10px;}
    
</style>
"""
# 注入 CSS (要貼在第一個 Markdown 之前)
st.markdown(custom_css, unsafe_allow_html=True)


# --- 主介面 Layout (新 Emoji & Text) ---

# Pretty Title with new emojis
st.title("🌸 家居單據智能分析 🎀")

# Cleaner introduction text
st.write("把雜亂的單據圖片（支援多張同時上傳）傳上來，AI 小助手就會瞬間為您分類並結算。")

# --- API Config (Unchanged, read from secrets) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("🔑 系統錯誤：找不到 API Key。請確保已在 Streamlit 的 Secrets 中設定 GEMINI_API_KEY。")
    st.stop()

MODEL_NAME = "gemini-3-flash-preview" 

# --- System Prompt (Unchanged) ---
SYSTEM_PROMPT = """
角色設定： 你是一個專業、細心且數學準確的個人財務助理。你的任務是整理每個月的消費單據，從上傳的圖片、PDF 或文字內容中提取資訊、自動分類並計算總結。

提取資訊： 讀取單據中的「日期」、「商戶名稱」及「總金額」。日期一律轉換為 YYYY-MM-DD 格式。

自動分類： 根據商戶性質歸入以下【指定類別】：
Pandamart / HKTVmall (對應平台訂單)
外出用餐費 (餐廳堂食、快餐、茶餐廳)
外賣費用 (外賣平台如 Foodpanda, KeeTa, Deliveroo 或到店自取)
超市食材費 (百佳、惠康、Market Place、AEON、街市等)
購物雜費 (服飾、電子產品、化妝品、文具等)
泊車費 (停車場、咪錶)
其他/未能分類 (無法歸類的項目，需簡述原因)

計算總結： 確保所有金額計算無誤。

輸出格式要求：
標題： 開首必須根據單據月份提供一個主題，例如「YYYY-MM 結算報告」。
Part 1：單據明細
格式：[YYYY-MM-DD] ：[商戶名稱] - $[金額] ([分類])

Part 2：月度結算報告
必須使用 Codebox (代碼框) 輸出。
必須按金額由高至低排列。
類別之間必須使用 ——— (三條長橫線) 分隔。
每個項目與分隔線之間需保留空行.

注意事項：
請勿使用 Markdown 表格，一律純文字排版。
輸出的內容中絕對不可包含任何 Citation (引用標記)。
若單據模糊，標註為 [需要人工確認]。
"""

# --- File Uploader Area ---
uploaded_files = st.file_uploader("📂 上傳單據圖片 (JPG, PNG, JPEG)", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if uploaded_files:
    st.info(f"💌 已準備好 {len(uploaded_files)} 張單據圖片囉！")
    
    # 這裡的 Button 就會套用上面定義好的 CSS
    if st.button("✨ 開始分析", key="analyze_button"):
        # Progress bar/spinner with a cute message
        with st.spinner("🍵 AI 小廚師正在仔細看您的單據，請稍候片刻..."):
            try:
                images = []
                for file in uploaded_files:
                    img = Image.open(file)
                    images.append(img)
                
                model = genai.GenerativeModel(MODEL_NAME)
                contents = [SYSTEM_PROMPT] + images
                response = model.generate_content(contents)
                
                st.success("✅ 分析完成囉！報告在這裡：")
                # 報告顯示區 (已使用純文字 pre 格式)
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"⚠️ 分析時發生錯誤（請確認是否上傳非圖片檔案）：{str(e)}")

else:
    # Gentle placeholder hint
    st.write("") # Empty space
    # st.write("🎀 準備好的時候就傳圖給我吧...") # 或者加這行 hint
