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
        if en > 0 and boy > 0:
            now_turkey = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Istanbul")).isoformat()

            data = {
                "en": en,
                "boy": boy,
                "tutar": tutar,
                "tarih": now_turkey
            }

            if ad_soyad:
                for col_name in ["ad_soyad", "musteri_adi", "musteri", "ad", "name"]:
                    try:
                        temp_data = data.copy()
                        temp_data[col_name] = ad_soyad
                        supabase.table("siparisler").insert(temp_data).execute()
                        st.success("Sipariş başarıyla kaydedildi!")
                        st.rerun()
                        break
                    except Exception:
                        continue
            else:
                try:
                    supabase.table("siparisler").insert(data).execute()
                    st.success("Sipariş kaydedildi.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Sipariş kaydedilemedi: {e}")
        else:
            st.warning("Lütfen En ve Boy değerlerini 0'dan büyük giriniz.")

st.divider()

# --- KAYITLI SİPARİŞLERİ LİSTELEME VE FİLTRELEME ---
st.header("Kayıtlı Siparişler")

try:
    response = supabase.table("siparisler").select("*").order("id", desc=True).execute()
    siparisler = response.data

    if siparisler:
        # Arama ve Filtreleme Barları
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            arama_metni = st.text_input("🔍 Müşteri Adına Göre Ara", placeholder="Müşteri adı giriniz...")
        with f_col2:
            tarih_secimi = st.date_input("📅 Tarih Aralığı Seçin", value=(), help="Başlangıç ve bitiş tarihi seçin")

        filtreli_siparisler = siparisler.copy()

        # 1. Müşteri İsmine Göre Filtrele
        if arama_metni:
            arama_kucuk = arama_metni.lower()
            yeni_liste = []
            for item in filtreli_siparisler:
                isim = str(
                    item.get("ad_soyad") or 
                    item.get("musteri_adi") or 
                    item.get("musteri") or 
                    item.get("ad") or 
                    item.get("name") or "İsimsiz Müşteri"
                ).lower()
                if arama_kucuk in isim:
                    yeni_liste.append(item)
            filtreli_siparisler = yeni_liste

        # 2. Tarih Aralığına Göre Filtrele
        if len(tarih_secimi) == 2:
            baslangic, bitis = tarih_secimi
            yeni_liste = []
            for item in filtreli_siparisler:
                tarih_str = item.get("tarih")
                if tarih_str:
                    try:
                        tarih_dt = datetime.datetime.fromisoformat(tarih_str).date()
                        if baslangic <= tarih_dt <= bitis:
                            yeni_liste.append(item)
                    except Exception:
                        yeni_liste.append(item)
            filtreli_siparisler = yeni_liste

        # Liste Kartları Gösterimi
        if filtreli_siparisler:
            # Toplam ciro ve m2 hesaplama
            toplam_tutar = sum(float(k.get("tutar", 0)) for k in filtreli_siparisler)
            toplam_m2 = sum(float(k.get("en", 0)) * float(k.get("boy", 0)) for k in filtreli_siparisler)
            
            toplam_tutar_formatted = f"{toplam_tutar:,.0f}".replace(",", ".")
            toplam_m2_formatted = f"{toplam_m2:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            # Özet Bilgi Kartları
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("Toplam Kayıt", f"{len(filtreli_siparisler)} Adet")
            m_col2.metric("Toplam Alan", f"{toplam_m2_formatted} m²")
            m_col3.metric("Toplam Tutar", f"{toplam_tutar_formatted} TL")

            st.divider()

            for k in filtreli_siparisler:
                siparis_id = k.get("id")
                ad = (
                    k.get("ad_soyad") or 
                    k.get("musteri_adi") or 
                    k.get("musteri") or 
                    k.get("ad") or 
                    k.get("name") or "İsimsiz Müşteri"
                )
                en_val = float(k.get("en", 0))
                boy_val = float(k.get("boy", 0))
                tutar_val = float(k.get("tutar", 0))
                m2_val = en_val * boy_val
                tarih_raw = k.get("tarih", "")

                # Tutar Formatlama (Örn: 586.608 TL)
                tutar_formatted = f"{tutar_val:,.0f}".replace(",", ".")

                tarih_formatted = ""
                if tarih_raw:
                    try:
                        dt = datetime.datetime.fromisoformat(tarih_raw)
                        tarih_formatted = dt.strftime("%d.%m.%Y %H:%M")
                    except Exception:
                        tarih_formatted = tarih_raw

                edit_key = f"edit_{siparis_id}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False

                with st.container(border=True):
                    if not st.session_state[edit_key]:
                        c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 0.5, 0.5])
                        with c1:
                            st.markdown(f"**Müşteri:** {ad}")
                            if tarih_formatted:
                                st.caption(f"📅 {tarih_formatted}")
                        with c2:
                            st.markdown(f"**Ölçü:** {en_val:.2f}m x {boy_val:.2f}m ({m2_val:.2f} m²)")
                        with c3:
                            st.markdown(f"**Tutar:** {tutar_formatted} TL")
                        with c4:
                            if st.button("✏️", key=f"btn_edit_{siparis_id}"):
                                st.session_state[edit_key] = True
                                st.rerun()
                        with c5:
                            if st.button("🗑️", key=f"btn_del_{siparis_id}"):
                                try:
                                    supabase.table("siparisler").delete().eq("id", siparis_id).execute()
                                    st.success("Kayıt silindi.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Silinemedi: {e}")
                    else:
                        st.markdown(f"**Düzenleniyor:** {ad}")
                        with st.form(f"form_edit_{siparis_id}"):
                            yeni_ad = st.text_input("Müşteri Adı Soyadı", value=ad)
                            e_col1, e_col2 = st.columns(2)
                            yeni_en = e_col1.number_input("En (m)", min_value=0.0, value=en_val, step=0.01)
                            yeni_boy = e_col2.number_input("Boy (m)", min_value=0.0, value=boy_val, step=0.01)
                            yeni_tutar = st.number_input("Tutar (TL)", min_value=0.0, value=tutar_val, step=10.0)

                            f_c1, f_c2 = st.columns(2)
                            with f_c1:
                                if st.form_submit_button("Kaydet ve Güncelle"):
                                    up_data = {"en": yeni_en, "boy": yeni_boy, "tutar": yeni_tutar}
                                    for key_name in ["ad_soyad", "musteri_adi", "musteri", "ad", "name"]:
                                        if key_name in k:
                                            up_data[key_name] = yeni_ad
                                            break
                                    try:
                                        supabase.table("siparisler").update(up_data).eq("id", siparis_id).execute()
                                        st.session_state[edit_key] = False
                                        st.success("Başarıyla güncellendi!")
                                        st.rerun()
                                    except Exception as ex:
                                        st.error(f"Güncellenemedi: {ex}")
                            with f_c2:
                                if st.form_submit_button("İptal"):
                                    st.session_state[edit_key] = False
                                    st.rerun()
        else:
            st.warning("Arama veya filtre kriterlerine uygun sipariş bulunamadı.")
    else:
        st.info("Henüz kayıtlı bir sipariş bulunmuyor.")

except Exception as e:
    st.error(f"Veri çekilirken bir hata oluştu: {e}")