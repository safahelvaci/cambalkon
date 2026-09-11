import streamlit as st
from supabase import create_client, Client
import datetime
import zoneinfo
import uuid

# Streamlit Sayfa Ayarları
st.set_page_config(page_title="Cam Balkon Sipariş Takip", layout="wide")

# --- ÖZEL CSS (Turuncu Başlık Banner ve Filigran) ---
st.markdown("""
    <style>
    .stApp {
        background-color: transparent;
    }
    .stApp::before {
        content: "Alaaddin HELVACI";
        position: fixed;
        top: 40%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-30deg);
        font-size: 80px;
        font-weight: bold;
        color: rgba(255, 255, 255, 0.04);
        white-space: nowrap;
        pointer-events: none;
        z-index: 0;
    }
    .header-banner {
        background-color: #ff6600;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }
    .header-banner h1 {
        color: #ffffff !important;
        margin: 0 !important;
        font-size: 38px !important;
        font-weight: 800 !important;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .header-banner h3 {
        color: #fff0e6 !important;
        margin-top: 5px !important;
        font-size: 20px !important;
        font-weight: 400 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Supabase Bağlantısı
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- TURUNCU BAŞLIK BANNERI ---
st.markdown("""
    <div class="header-banner">
        <h1>MAKRO CAMBALKON</h1>
        <h3>Cam Balkon Sipariş & Müşteri Takip</h3>
    </div>
""", unsafe_allow_html=True)

# Metni Sayıya Çevirme Yardımcı Fonksiyonu
def metinden_tam_sayiya(val_str):
    if not val_str:
        return 0
    temiz = str(val_str).replace(".", "").replace(",", "").strip()
    try:
        return int(float(temiz))
    except ValueError:
        return 0

# Binlik Noktalı Formatlama (Örn: 3000 -> 3.000 TL)
def format_tam_tl(sayi):
    if sayi <= 0:
        return "0"
    return f"{int(round(sayi)):,.0f}".replace(",", ".")

# Metrekare Fiyatı için Otomatik Noktalama Callback Fonksiyonu
def m2_fiyat_formatla():
    ham_deger = st.session_state.get("m2_fiyat_input", "")
    sayi = metinden_tam_sayiya(ham_deger)
    if sayi > 0:
        st.session_state["m2_fiyat_input"] = format_tam_tl(sayi)

# Resim Yükleme Yardımcı Fonksiyonu
def resim_yukle(yuklenen_dosya):
    if yuklenen_dosya is not None:
        try:
            dosya_uzantisi = yuklenen_dosya.name.split(".")[-1]
            benzersiz_isim = f"{uuid.uuid4()}.{dosya_uzantisi}"
            dosya_baytlari = yuklenen_dosya.getvalue()
            
            supabase.storage.from_("resimler").upload(
                file=dosya_baytlari,
                path=benzersiz_isim,
                file_options={"content-type": yuklenen_dosya.type}
            )
            
            resim_url = supabase.storage.from_("resimler").get_public_url(benzersiz_isim)
            return resim_url
        except Exception as e:
            st.error(f"Resim yüklenirken hata oluştu: {e}")
            return None
    return None

# Session State İlk Tanımlama
if "m2_fiyat_input" not in st.session_state:
    st.session_state["m2_fiyat_input"] = ""

# Sabit Listeler
CAM_RENKLERI = ["Şeffaf", "Füme", "Mavi", "Yeşil", "Bronz"]
ALUMINYUM_RENKLERI = ["Siyah", "Füme", "Beyaz", "Eloksal (Gri)", "Ahşap Desenli"]
SIPARIS_DURUMLARI = ["⏳ Beklemede", "✅ Onaylandı", "❌ İptal Edildi"]

# --- MÜŞTERİ / SİPARİŞ EKLEME FORMU ---
st.header("Yeni Sipariş Ekle")

col_ad, col_durum = st.columns([2, 1])
ad_soyad = col_ad.text_input("Müşteri Adı Soyadı")
siparis_durumu = col_durum.selectbox("📋 Sipariş Durumu", SIPARIS_DURUMLARI, index=0)

col1, col2, col3 = st.columns(3)
en = col1.number_input("En (m)", min_value=0.0, step=0.01)
boy = col2.number_input("Boy (m)", min_value=0.0, step=0.01)

m2_fiyat_str = col3.text_input(
    "Metrekare Fiyatı (TL)", 
    key="m2_fiyat_input", 
    on_change=m2_fiyat_formatla
)

# Renk Seçenekleri Kutuları
r_col1, r_col2 = st.columns(2)
cam_rengi = r_col1.selectbox("🎨 Cam Rengi", CAM_RENKLERI)
aluminyum_rengi = r_col2.selectbox("🖌️ Alüminyum Rengi", ALUMINYUM_RENKLERI)

# Proje / Ölçü Çizimi Resim Yükleme
proje_resmi = st.file_uploader("🖼️ Proje / Ölçü Çizimi Ekle (İsteğe Bağlı)", type=["png", "jpg", "jpeg"])

m2_fiyat = metinden_tam_sayiya(m2_fiyat_str)

hesaplanan_m2 = en * boy
hesaplanan_tutar = hesaplanan_m2 * m2_fiyat

if en > 0 and boy > 0 and m2_fiyat > 0:
    tutar_yazi = format_tam_tl(hesaplanan_tutar)
    m2_fiyat_yazi = format_tam_tl(m2_fiyat)
    st.info(f"📐 **Hesaplanan Alan:** {hesaplanan_m2:.2f} m² | 💵 **m² Fiyatı:** {m2_fiyat_yazi} TL | 💰 **Otomatik Toplam Tutar:** {tutar_yazi} TL")

with st.form("siparis_formu", clear_on_submit=True):
    submit = st.form_submit_button("Siparişi Kaydet")

    if submit:
        if en > 0 and boy > 0 and m2_fiyat > 0:
            now_turkey = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Istanbul")).isoformat()
            
            resim_url = resim_yukle(proje_resmi)

            data = {
                "en": en,
                "boy": boy,
                "tutar": round(hesaplanan_tutar),
                "odenen": 0,
                "cam_rengi": cam_rengi,
                "aluminyum_rengi": aluminyum_rengi,
                "tarih": now_turkey,
                "resim_url": resim_url,
                "durum": siparis_durumu
            }

            if ad_soyad:
                for col_name in ["ad_soyad", "musteri_adi", "musteri", "ad", "name"]:
                    try:
                        temp_data = data.copy()
                        temp_data[col_name] = ad_soyad
                        supabase.table("siparisler").insert(temp_data).execute()
                        st.success(f"Sipariş başarıyla kaydedildi! (Durum: {siparis_durumu} | Toplam Tutar: {format_tam_tl(hesaplanan_tutar)} TL)")
                        st.session_state["m2_fiyat_input"] = ""
                        st.rerun()
                        break
                    except Exception:
                        continue
            else:
                try:
                    supabase.table("siparisler").insert(data).execute()
                    st.success("Sipariş kaydedildi.")
                    st.session_state["m2_fiyat_input"] = ""
                    st.rerun()
                except Exception as e:
                    st.error(f"Sipariş kaydedilemedi: {e}")
        else:
            st.warning("Lütfen En, Boy ve Metrekare Fiyatı değerlerini 0'dan büyük giriniz.")

st.divider()

# --- KAYITLI SİPARİŞLERİ LİSTELEME VE DÜZENLEME ---
st.header("Kayıtlı Siparişler ve Borç Takibi")

try:
    response = supabase.table("siparisler").select("*").order("id", desc=True).execute()
    siparisler = response.data

    if siparisler:
        f_col1, f_col2, f_col3 = st.columns([2, 2, 1.5])
        with f_col1:
            arama_metni = st.text_input("🔍 Müşteri Adına Göre Ara", placeholder="Müşteri adı giriniz...")
        with f_col2:
            tarih_secimi = st.date_input("📅 Tarih Aralığı Seçin", value=(), help="Başlangıç ve bitiş tarihi seçin")
        with f_col3:
            durum_filtresi = st.selectbox("📋 Duruma Göre Filtrele", ["Tümü"] + SIPARIS_DURUMLARI)

        filtreli_siparisler = siparisler.copy()

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

        if durum_filtresi != "Tümü":
            filtreli_siparisler = [item for item in filtreli_siparisler if item.get("durum") == durum_filtresi]

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

        if filtreli_siparisler:
            toplam_tutar = sum(float(k.get("tutar", 0)) for k in filtreli_siparisler)
            toplam_odenen = sum(float(k.get("odenen", 0) or 0) for k in filtreli_siparisler)
            toplam_kalan = toplam_tutar - toplam_odenen

            # Özet Bilgi Kartları
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Toplam Kayıt", f"{len(filtreli_siparisler)} Adet")
            m_col2.metric("Toplam Tutar", f"{format_tam_tl(toplam_tutar)} TL")
            m_col3.metric("Tahsil Edilen", f"{format_tam_tl(toplam_odenen)} TL")
            m_col4.metric("Kalan Toplam Alacak", f"{format_tam_tl(toplam_kalan)} TL")

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
                odenen_val = float(k.get("odenen", 0) or 0)
                cam_val = k.get("cam_rengi", "Belirtilmedi")
                alum_val = k.get("aluminyum_rengi", "Belirtilmedi")
                resim_url_val = k.get("resim_url")
                durum_val = k.get("durum", "⏳ Beklemede")
                
                kalan_val = tutar_val - odenen_val
                m2_val = en_val * boy_val
                m2_birim_fiyat = (tutar_val / m2_val) if m2_val > 0 else 0

                tarih_raw = k.get("tarih", "")
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

                # Durum ve Bakiye Bilgisi İçeren Başlık
                bakiye_durumu = f"🔴 Kalan: {format_tam_tl(kalan_val)} TL" if kalan_val > 0 else "🟢 Borcu Yok"
                expander_label = f"👤 {ad}   |   [{durum_val}]   |   {bakiye_durumu}"

                with st.expander(expander_label, expanded=False):
                    if not st.session_state[edit_key]:
                        c1, c2, c3, c4, c5 = st.columns([3, 2.5, 3, 0.5, 0.5])
                        with c1:
                            if tarih_formatted:
                                st.caption(f"📅 Sipariş Tarihi: {tarih_formatted}")
                            st.markdown(f"📋 **Sipariş Durumu:** `{durum_val}`")
                            st.markdown(f"📏 **Ölçü:** {en_val:.2f}m x {boy_val:.2f}m ({m2_val:.2f} m²)")
                            st.markdown(f"💵 **m² Fiyatı:** {format_tam_tl(m2_birim_fiyat)} TL")
                            st.markdown(f"🎨 **Cam:** {cam_val} | 🖌️ **Alüminyum:** {alum_val}")
                            
                            # Yüklenmiş Proje Resmi Varsa Göster
                            if resim_url_val:
                                st.markdown("**📐 Proje Çizimi:**")
                                st.image(resim_url_val, use_container_width=True)

                        with c2:
                            st.markdown(f"💵 **Toplam Borç:** {format_tam_tl(tutar_val)} TL")
                            st.markdown(f"✅ **Ödenen:** {format_tam_tl(odenen_val)} TL")
                            if kalan_val > 0:
                                st.markdown(f"🔴 **Kalan Bakiye:** <span style='color:red; font-weight:bold;'>{format_tam_tl(kalan_val)} TL</span>", unsafe_allow_html=True)
                            else:
                                st.markdown("🟢 **Ödeme Tamamlandı (Borcu Yok)**")

                            # --- ÖDEME GEÇMİŞİ LİSTELEME ---
                            st.markdown("---")
                            st.markdown("**📜 Ödeme Geçmişi:**")
                            try:
                                odeme_res = supabase.table("odemeler").select("*").eq("siparis_id", siparis_id).order("tarih", desc=True).execute()
                                odeme_listesi = odeme_res.data
                                if odeme_listesi:
                                    for od in odeme_listesi:
                                        o_tutar = float(od.get("tutar", 0))
                                        o_tarih_raw = od.get("tarih", "")
                                        o_tarih_fmt = ""
                                        if o_tarih_raw:
                                            try:
                                                o_dt = datetime.datetime.fromisoformat(o_tarih_raw)
                                                o_tarih_fmt = o_dt.strftime("%d.%m.%Y")
                                            except Exception:
                                                o_tarih_fmt = o_tarih_raw
                                        st.caption(f"• **{o_tarih_fmt}:** {format_tam_tl(o_tutar)} TL")
                                else:
                                    st.caption("Henüz yapılmış bir ödeme kaydı yok.")
                            except Exception:
                                st.caption("Ödeme geçmişi yüklenemedi.")

                        with c3:
                            with st.popover("💳 Ödeme / Taksit Ekle"):
                                with st.form(f"odeme_form_{siparis_id}"):
                                    yeni_odeme_str = st.text_input("Ödenen Tutar (TL)", key=f"pay_in_{siparis_id}")
                                    odeme_tarihi = st.date_input("Ödeme Tarihi", value=datetime.date.today(), key=f"pay_date_{siparis_id}")
                                    
                                    if st.form_submit_button("Ödemeyi Kaydet"):
                                        yeni_odeme = metinden_tam_sayiya(yeni_odeme_str)
                                        if yeni_odeme > 0:
                                            guncel_odenen = odenen_val + yeni_odeme
                                            secilen_odeme_tarihi = datetime.datetime.combine(odeme_tarihi, datetime.time(12, 0)).isoformat()
                                            
                                            try:
                                                supabase.table("siparisler").update({"odenen": guncel_odenen}).eq("id", siparis_id).execute()
                                                supabase.table("odemeler").insert({
                                                    "siparis_id": siparis_id,
                                                    "tutar": yeni_odeme,
                                                    "tarih": secilen_odeme_tarihi
                                                }).execute()

                                                st.success(f"{odeme_tarihi.strftime('%d.%m.%Y')} tarihinde {format_tam_tl(yeni_odeme)} TL ödeme kaydedildi.")
                                                st.rerun()
                                            except Exception as ex:
                                                st.error(f"Ödeme kaydedilemedi: {ex}")
                                        else:
                                            st.warning("Geçerli bir tutar giriniz.")

                        with c4:
                            if st.button("✏️", key=f"btn_edit_{siparis_id}", help="Siparişi Düzenle"):
                                st.session_state[edit_key] = True
                                st.rerun()

                        with c5:
                            if st.button("🗑️", key=f"btn_del_{siparis_id}", help="Siparişi Sil"):
                                try:
                                    supabase.table("siparisler").delete().eq("id", siparis_id).execute()
                                    st.success("Kayıt silindi.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Silinemedi: {e}")

                    else:
                        # Düzenleme Modu
                        st.markdown(f"**Düzenleniyor:** {ad}")
                        with st.form(f"form_edit_{siparis_id}"):
                            yeni_ad = st.text_input("Müşteri Adı Soyadı", value=ad)
                            
                            yeni_durum = st.selectbox("📋 Sipariş Durumu", SIPARIS_DURUMLARI, index=SIPARIS_DURUMLARI.index(durum_val) if durum_val in SIPARIS_DURUMLARI else 0)

                            e_col1, e_col2, e_col3 = st.columns(3)
                            yeni_en = e_col1.number_input("En (m)", min_value=0.0, value=en_val, step=0.01)
                            yeni_boy = e_col2.number_input("Boy (m)", min_value=0.0, value=boy_val, step=0.01)
                            
                            varsayilan_m2_str = format_tam_tl(m2_birim_fiyat)
                            yeni_m2_fiyat_str = e_col3.text_input("Metrekare Fiyatı (TL)", value=varsayilan_m2_str)

                            er_col1, er_col2 = st.columns(2)
                            yeni_cam = er_col1.selectbox("🎨 Cam Rengi", CAM_RENKLERI, index=CAM_RENKLERI.index(cam_val) if cam_val in CAM_RENKLERI else 0)
                            yeni_alum = er_col2.selectbox("🖌️ Alüminyum Rengi", ALUMINYUM_RENKLERI, index=ALUMINYUM_RENKLERI.index(alum_val) if alum_val in ALUMINYUM_RENKLERI else 0)

                            yeni_proje_resmi = st.file_uploader("🖼️ Yeni Proje Resmi Yükle", type=["png", "jpg", "jpeg"], key=f"edit_img_{siparis_id}")

                            yeni_m2_fiyat = metinden_tam_sayiya(yeni_m2_fiyat_str)
                            yeni_hesaplanan_tutar = yeni_en * yeni_boy * yeni_m2_fiyat
                            st.caption(f"Yeni Toplam Tutar: {format_tam_tl(yeni_hesaplanan_tutar)} TL")

                            f_c1, f_c2 = st.columns(2)
                            with f_c1:
                                if st.form_submit_button("Kaydet ve Güncelle"):
                                    up_data = {
                                        "en": yeni_en, 
                                        "boy": yeni_boy, 
                                        "tutar": round(yeni_hesaplanan_tutar),
                                        "cam_rengi": yeni_cam,
                                        "aluminyum_rengi": yeni_alum,
                                        "durum": yeni_durum
                                    }
                                    
                                    if yeni_proje_resmi:
                                        yeni_url = resim_yukle(yeni_proje_resmi)
                                        if yeni_url:
                                            up_data["resim_url"] = yeni_url

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