import streamlit as st
from supabase import create_client, Client
import datetime
import zoneinfo

# Streamlit Sayfa Ayarları
st.set_page_config(page_title="Cam Balkon Sipariş Takip", layout="wide")

# Supabase Bağlantısı
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

st.title("🧱 Cam Balkon Sipariş Takip Sistemi")

# --- SİPARİŞ EKLEME FORMU ---
with st.expander("➕ Yeni Sipariş Ekle", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        musteri = st.text_input("Müşteri Adı / Soyadı")
        en = st.number_input("En (Metre)", min_value=0.0, step=0.1, format="%.2f")
        boy = st.number_input("Boy (Metre)", min_value=0.0, step=0.1, format="%.2f")
    with col2:
        fiyat = st.number_input("m² Fiyatı (TL)", min_value=0.0, step=50.0, format="%.2f")
    
    if st.button("Siparişi Hesapla ve Kaydet"):
        if musteri and en > 0 and boy > 0 and fiyat > 0:
            m2 = en * boy
            tutar = m2 * fiyat
            
            # Türkiye Saati Ayarı (UTC+3)
            turkiye_saati = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Istanbul"))
            tarih = turkiye_saati.strftime("%d.%m.%Y %H:%M")
            
            # Supabase'e Veri Ekleme
            supabase.table("siparisler").insert({
                "musteri": musteri,
                "en": en,
                "boy": boy,
                "metrekare": m2,
                "tutar": tutar,
                "tarih": tarih
            }).execute()
            
            st.success(f"{musteri} siparişi başarıyla kaydedildi! ({m2:.2f} m² - {tutar:.2f} TL)")
            st.rerun()
        else:
            st.error("Lütfen tüm alanları eksiksiz doldurun.")

st.divider()

# --- KAYITLI SİPARİŞLERİ LİSTELEME ---
st.subheader("📋 Kayıtlı Siparişler")

try:
    response = supabase.table("siparisler").select("*").execute()
    kayitlar = response.data
    
    if kayitlar:
        kayitlar = sorted(kayitlar, key=lambda x: x.get('id', 0), reverse=True)

  if kayitlar:
            for k in kayitlar:
                siparis_id = k.get("id")
                ad_soyad = k.get("ad_soyad", "")
                tarih_val = k.get("tarih", "")
                en_val = k.get("en", 0.0)
                boy_val = k.get("boy", 0.0)
                m2_val = en_val * boy_val if en_val and boy_val else 0.0
                tutar_val = k.get("tutar", 0.0)

                with st.container(border=True):
                    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1])
                    c1.write(f"**Müşteri:** {ad_soyad}")
                    c2.write(f"**Ölçü:** {en_val:.2f}m x {boy_val:.2f}m ({m2_val:.2f} m²)")
                    c3.write(f"**Tutar:** {tutar_val:.2f} TL")
                    
                    # Düzenleme Modu Kontrolü
                    edit_key = f"edit_mode_{siparis_id}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = False

                    if c4.button("✏️", key=f"btn_edit_{siparis_id}", help="Düzenle"):
                        st.session_state[edit_key] = not st.session_state[edit_key]

                    if c5.button("🗑️", key=f"sil_{siparis_id}", help="Sil"):
                        supabase.table("siparisler").delete().eq("id", siparis_id).execute()
                        st.success("Kayıt silindi!")
                        st.rerun()

                    # Düzenleme Formu
                    if st.session_state[edit_key]:
                        with st.form(key=f"form_edit_{siparis_id}"):
                            yeni_ad = st.text_input("Müşteri Ad Soyad", value=ad_soyad)
                            col_e, col_b = st.columns(2)
                            yeni_en = col_e.number_input("En (m)", value=float(en_val), step=0.01)
                            yeni_boy = col_b.number_input("Boy (m)", value=float(boy_val), step=0.01)
                            yeni_tutar = st.number_input("Tutar (TL)", value=float(tutar_val), step=10.0)
                            
                            if st.form_submit_button("Kaydet ve Güncelle"):
                                supabase.table("siparisler").update({
                                    "ad_soyad": yeni_ad,
                                    "en": yeni_en,
                                    "boy": yeni_boy,
                                    "tutar": yeni_tutar
                                }).eq("id", siparis_id).execute()
                                
                                st.session_state[edit_key] = False
                                st.success("Müşteri bilgileri başarıyla güncellendi!") 
                                else:
                                    st.info("Henüz kayıtlı sipariş bulunmuyor.")