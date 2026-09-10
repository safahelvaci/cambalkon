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

st.title("Cam Balkon Sipariş & Müşteri Takip")

# --- MÜŞTERİ / SİPARİŞ EKLEME FORMU ---
st.header("Yeni Sipariş Ekle")
with st.form("siparis_formu", clear_on_submit=True):
    ad_soyad = st.text_input("Müşteri Adı Soyadı")
    col1, col2 = st.columns(2)
    en = col1.number_input("En (m)", min_value=0.0, step=0.01)
    boy = col2.number_input("Boy (m)", min_value=0.0, step=0.01)
    tutar = st.number_input("Tutar (TL)", min_value=0.0, step=10.0)
    
    submit = st.form_submit_button("Siparişi Kaydet")

    if submit:
        if ad_soyad and en > 0 and boy > 0:
            now_turkey = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Istanbul")).isoformat()
            
            # Esnek Kayıt Sözlüğü
            data = {
                "ad_soyad": ad_soyad,
                "en": en,
                "boy": boy,
                "tutar": tutar,
                "tarih": now_turkey
            }
            
            try:
                supabase.table("siparisler").insert(data).execute()
                st.success("Sipariş başarıyla kaydedildi!")
                st.rerun()
            except Exception as insert_error:
                # Eger ad_soyad sutunu veritabaninda yoksa musteri_adi ile dener
                try:
                    alt_data = {
                        "musteri_adi": ad_soyad,
                        "en": en,
                        "boy": boy,
                        "tutar": tutar,
                        "tarih": now_turkey
                    }
                    supabase.table("siparisler").insert(alt_data).execute()
                    st.success("Sipariş başarıyla kaydedildi!")
                    st.rerun()
                except Exception as final_error:
                    st.error(f"Kayıt eklenirken hata oluştu: {final_error}")
        else:
            st.warning("Lütfen müşteri adını ve ölçüleri eksiksiz girin.")

st.divider()

# --- MÜŞTERİ / SİPARİŞ LİSTELEME, DÜZENLEME VE SİLME ---
st.header("Kayıtlı Siparişler")

try:
    response = supabase.table("siparisler").select("*").order("id", desc=True).execute()
    kayitlar = response.data

    if kayitlar:
        for k in kayitlar:
            siparis_id = k.get("id")
            
            # Farklı olabilecek müşteri adı sütun isimlerini kontrol etme
            ad_soyad_val = k.get("ad_soyad") or k.get("musteri_adi") or k.get("ad") or "İsimsiz Müşteri"
            
            # Tarih Formatlama
            tarih_raw = k.get("tarih") or k.get("created_at") or ""
            tarih_str = ""
            if tarih_raw:
                try:
                    dt = datetime.datetime.fromisoformat(str(tarih_raw).replace('Z', '+00:00'))
                    tarih_str = dt.strftime("%d.%m.%Y %H:%M")
                except Exception:
                    tarih_str = str(tarih_raw)[:16]

            en_val = k.get("en", 0.0)
            boy_val = k.get("boy", 0.0)
            m2_val = en_val * boy_val if en_val and boy_val else 0.0
            tutar_val = k.get("tutar", 0.0)

            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 1, 1])
                
                # Müşteri Adı ve Tarih Gösterimi
                if tarih_str:
                    c1.write(f"**Müşteri:** {ad_soyad_val}\n\n*📅 {tarih_str}*")
                else:
                    c1.write(f"**Müşteri:** {ad_soyad_val}")
                    
                c2.write(f"**Ölçü:** {en_val:.2f}m x {boy_val:.2f}m ({m2_val:.2f} m²)")
                c3.write(f"**Tutar:** {tutar_val:.2f} TL")
                
                # Düzenleme Modu Durum Kontrolü
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
                        yeni_ad = st.text_input("Müşteri Ad Soyad", value=ad_soyad_val)
                        col_e, col_b = st.columns(2)
                        yeni_en = col_e.number_input("En (m)", value=float(en_val), step=0.01)
                        yeni_boy = col_b.number_input("Boy (m)", value=float(boy_val), step=0.01)
                        yeni_tutar = st.number_input("Tutar (TL)", value=float(tutar_val), step=10.0)
                        
                        if st.form_submit_button("Kaydet ve Güncelle"):
                            # Güncelleme sırasında sütun kontrolü
                            update_data = {"en": yeni_en, "boy": yeni_boy, "tutar": yeni_tutar}
                            if "ad_soyad" in k:
                                update_data["ad_soyad"] = yeni_ad
                            elif "musteri_adi" in k:
                                update_data["musteri_adi"] = yeni_ad
                            else:
                                update_data["ad_soyad"] = yeni_ad

                            supabase.table("siparisler").update(update_data).eq("id", siparis_id).execute()
                            
                            st.session_state[edit_key] = False
                            st.success("Müşteri bilgileri başarıyla güncellendi!")
                            st.rerun()
    else:
        st.info("Henüz kayıtlı sipariş bulunmuyor.")

except Exception as e:
    st.error(f"Veri çekilirken bir hata oluştu: {e}")