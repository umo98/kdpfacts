import streamlit as st
import requests
import json
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import urllib.request

# Sayfa ayarları
st.set_page_config(page_title="Çocuklar İçin Bilgi Kitabı", page_icon="🤠")

# OpenRouter API fonksiyonu
def generate_facts(api_key, topic):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    prompt = f"""
    Create exactly 28 fun facts about '{topic}' for kids aged 8-12.
    STRICT RULES FOR EACH FACT:
    1. Exactly 3 sentences per fact.
    2. Exactly 20 to 24 words in total per fact.
    3. Must be fun and engaging for children.
    4. Return ONLY a JSON array of strings like ["Fact 1", "Fact 2", ... "Fact 28"]. No other text.
    """
    
    payload = {
        "model": "openrouter/owl-alpha",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        content = result['choices'][0]['message']['content']
        # JSON formatını temizle
        if content.startswith("```json"):
            content = content[7:-3].strip()
        facts = json.loads(content)
        return facts
    else:
        st.error(f"API Hatası: {response.text}")
        return None

# Görsel oluşturma fonksiyonu
def create_page_image(facts_4, font_path):
    # 6x9 inç, 150 DPI (900x1350 piksel)
    width, height = 900, 1350
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(font_path, 28)
        font_star = ImageFont.truetype(font_path, 36)
    except:
        font = ImageFont.load_default()
        font_star = ImageFont.load_default()

    margin_x = 80
    margin_y = 60
    box_width = width - (2 * margin_x)
    box_height = 270
    gap = 40
    
    # Kutu rengi (Açık mavi)
    box_color = "#D6EAF8"
    text_color = "#2C3E50"
    line_color = "#7F8C8D"

    for i, fact in enumerate(facts_4):
        y_start = margin_y + i * (box_height + gap)
        
        # Açık mavi kutuyu çiz
        draw.rounded_rectangle(
            [margin_x, y_start, margin_x + box_width, y_start + box_height],
            radius=20, fill=box_color
        )
        
        # Yazıyı ortala (Kelime kaydırma ile)
        max_text_width = box_width - 40
        words = fact.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_text_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)
        
        # Satır yüksekliğini hesapla ve dikey ortala
        line_height = draw.textbbox((0, 0), "Ay", font=font)[3] - draw.textbbox((0, 0), "Ay", font=font)[1]
        total_text_height = len(lines) * (line_height + 10)
        y_text = y_start + (box_height - total_text_height) / 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x_text = margin_x + (box_width - line_width) / 2
            draw.text((x_text, y_text), line.strip(), font=font, fill=text_color)
            y_text += line_height + 10
            
        # Ayırıcı çizgi ve yıldız (son kutu hariç)
        if i < 3:
            line_y = y_start + box_height + (gap / 2)
            mid_x = width / 2
            
            draw.line([(margin_x, line_y), (mid_x - 30, line_y)], fill=line_color, width=2)
            draw.text((mid_x - 10, line_y - 15), "★", font=font_star, fill=line_color)
            draw.line([(mid_x + 30, line_y), (width - margin_x, line_y)], fill=line_color, width=2)
            
    return img

# Ana Streamlit Uygulaması
st.title("📚 Çocuklar İçin Bilgi Kitabı Tasarlayıcı")
st.markdown("8-12 yaş arası çocuklar için 7 sayfalık (28 bilgi) eğlenceli bir kitap oluşturun!")

api_key = st.text_input("OpenRouter API Anahtarınızı Girin:", type="password")
topic = st.text_input("Kitabın Konusu (Örn: Cowboy, Uzay, Dinozor):")

if st.button("Kitabı Oluştur"):
    if not api_key or not topic:
        st.warning("Lütfen API anahtarını ve konuyu girin!")
    else:
        with st.spinner("Yapay zeka bilgileri yazıyor... (Bu biraz zaman alabilir)"):
            # Font indirme (Sistemlerde font sorunu olmaması için)
            font_path = "Roboto-Regular.ttf"
            if not os.path.exists(font_path):
                urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf", font_path)
            
            facts = generate_facts(api_key, topic)
            
            if facts and len(facts) == 28:
                st.success("28 bilgi başarıyla oluşturuldu! Sayfalar çiziliyor...")
                images = []
                
                for page_num in range(7):
                    start_idx = page_num * 4
                    end_idx = start_idx + 4
                    page_facts = facts[start_idx:end_idx]
                    
                    img = create_page_image(page_facts, font_path)
                    images.append(img)
                    
                    # Ekranda göster
                    st.image(img, caption=f"Sayfa {page_num + 1}")
                    
                    # İndirme butonu
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PNG")
                    st.download_button(
                        label=f"📥 Sayfa {page_num + 1} İndir (PNG)",
                        data=img_bytes.getvalue(),
                        file_name=f"sayfa_{page_num + 1}.png",
                        mime="image/png"
                    )
            elif facts:
                st.error(f"Beklenen 28 bilgi yerine {len(facts)} bilgi geldi. Lütfen tekrar deneyin.")
