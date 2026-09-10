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
            musteri_val = k.get("musteri", "")
            en_val = k.get("en", 0.0)
            boy_val = k.get("boy", 0.0)
            m2 = k.get("metrekare", 0.0)
            tutar_val = k.get("tutar", 0.0)
            tarih_val = k.get("tarih", "")

            with st.container(border=True):
                c1, c2, c3, c4, c5, c6 = st.columns([2, 1, 1.5, 2, 1.5, 1])
                with c1:
                    st.write(f"**Müşteri:** {musteri_val}")
                with c2:
                    st.write(f"**ID:** #{siparis_id}")
                with c3:
                    st.write(f"**Tarih:** 📅 {tarih_val}")
                with c4:
                    st.write(f"**Ölçü:** {en_val:.2f}m x {boy_val:.2f}m ({m2:.2f} m²)")
                with c5:
                    st.write(f"**Tutar:** {tutar_val:.2f} TL")
                with c6:
                    if st.button("🗑️ Sil", key=f"sil_{siparis_id}"):
                        supabase.table("siparisler").delete().eq("id", siparis_id).execute()
                        st.rerun()
    else:
        st.info("Henüz kayıtlı sipariş bulunmuyor.")

except Exception as e:
    st.error(f"Veri çekilirken bir hata oluştu: {e}")