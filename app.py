import streamlit as st
import google.generativeai as genai
from PIL import Image

# 網頁基本設定
st.set_page_config(page_title="家居單據智能分析工具", page_icon="🧾", layout="centered")

st.title("🧾 家居單據智能分析工具")
st.write("請上傳需要分析的單據圖片（支援多張同時上傳），系統會自動為您分類並結算。")

# 設定 Gemini API Key (從 Streamlit Secrets 讀取)
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except KeyError:
    st.error("系統錯誤：找不到 API Key。請確保已在 Streamlit 的 Secrets 中設定 GEMINI_API_KEY。")
    st.stop()

# 選擇模型 (使用你截圖中確定可用的模型)
MODEL_NAME = "gemini-3-flash-preview" 

# 核心 Prompt (你的原本設定)
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
每個項目與分隔線之間需保留空行。

注意事項：
請勿使用 Markdown 表格，一律純文字排版。
輸出的內容中絕對不可包含任何 Citation (引用標記)。
若單據模糊，標註為 [需要人工確認]。
"""

# 上傳檔案元件
uploaded_files = st.file_uploader("上傳單據圖片 (JPG, PNG, JPEG)", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

if uploaded_files:
    st.info(f"已準備 {len(uploaded_files)} 張單據")
    
    if st.button("✨ 開始分析", use_container_width=True):
        with st.spinner("AI 正在努力分析單據中，請稍候..."):
            try:
                # 準備所有圖片
                images = []
                for file in uploaded_files:
                    img = Image.open(file)
                    images.append(img)
                
                # 呼叫 Gemini
                model = genai.GenerativeModel(MODEL_NAME)
                
                # 將 Prompt 和所有圖片打包發送
                contents = [SYSTEM_PROMPT] + images
                response = model.generate_content(contents)
                
                # 顯示結果
                st.success("分析完成！")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"分析時發生錯誤：{str(e)}")
