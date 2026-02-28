import streamlit as st
import pandas as pd
from datetime import datetime

# DiveLogic dosyasının varlığını kontrol et
try:
    from dive_logic import DiveLogic
except ImportError:
    st.error("HATA: 'dive_logic.py' dosyası bulunamadı! Lütfen GitHub'a bu dosyayı da yükleyin.")

st.set_page_config(page_title="EGM Dalış Planlayıcı Pro", layout="wide", page_icon="🤿")

# --- OTURUM HAFIZASI (Session State) BAŞLATMA ---
if 'last_group' not in st.session_state:
    st.session_state['last_group'] = 'A'
if 'history' not in st.session_state:
    st.session_state['history'] = []

def check_egm_compliance(system, d_m, d_f, gas, pers):
    alerts = []
    if system == "SCUBA":
        if d_f > 140: alerts.append("❌ KRİTİK: Scuba ile 140 ft (42m) sınırı aşılamaz!")
        if pers < 3: alerts.append("👥 EKİP: En az 3 personel bulunmalıdır.")
    elif system == "SİDS":
        if d_f > 190: alerts.append("❌ KRİTİK: SİDS 190 ft (58m) sınırı aşıldı!")
        if pers < 4: alerts.append("👥 EKİP: En az 4 personel gereklidir.")
        if d_f > 33 and pers < 7: alerts.append("👥 EKİP: 10m üzeri derinlikte ekip en az 7 kişi olmalıdır.")
    elif system == "NİTROKS":
        try:
            o2 = int(gas)
            if o2 == 32 and d_m > 33: alerts.append("❌ MEVZUAT: %32 Nitroks sınırı 33 metredir.")
            if o2 == 36 and d_m > 28: alerts.append("❌ MEVZUAT: %36 Nitroks sınırı 28 metredir.")
        except: pass
    return alerts

st.title("🤿 US NAVY Rev 7 / EGM Profesyonel Dalış Planlayıcı")
st.markdown("---")

tab1, tab2 = st.tabs(["🟦 İLK DALIŞ PLANI", "🟩 MÜKERRER DALIŞ ANALİZİ"])

# --- TAB 1: İLK DALIŞ ---
with tab1:
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.subheader("Giriş Parametreleri")
        sys_type = st.selectbox("Dalış Sistemi", ["SCUBA", "SİDS", "NİTROKS", "KDDS"], key="sys1")
        d_m = st.number_input("Derinlik (Metre)", value=21.0, step=0.5, key="dm1")
        d_f = d_m * 3.28084
        b_t = st.number_input("Dip Zamanı (Dakika)", value=40, step=1, key="bt1")
        alt = st.number_input("İrtifa (Feet)", value=0, step=500, key="alt1")
        pers = st.number_input("Personel Sayısı", value=4, key="p1")
        gas = st.text_input("Gaz (%O2)", value="21", key="g1")
        
        st.write("---")
        t_v = st.number_input("Tüp Hacmi (L)", value=12, key="tv1")
        t_p = st.number_input("Başlangıç Basıncı (Bar)", value=200, key="tp1")
        
        calc_btn = st.button("HESAPLA VE RAPORLA", type="primary", use_container_width=True)

    with c2:
        if calc_btn:
            st.subheader("📋 DETAYLI DALIŞ RAPORU")
            
            # Mevzuat
            alerts = check_egm_compliance(sys_type, d_m, d_f, gas, pers)
            for a in alerts: st.error(a)
            if not alerts: st.success("✅ EGM MEVZUATINA UYGUNDUR")

            # Hesaplamalar
            equiv_d = DiveLogic.get_altitude_correction(d_f, alt)
            ndl = DiveLogic.get_ndl(equiv_d)
            
            # Sonuç Kutuları
            r1, r2, r3 = st.columns(3)
            r1.metric("Eşdeğer Derinlik", f"{equiv_d:.1f} ft")
            r2.metric("NDL Sınırı", f"{ndl} dk")
            
            # Deko Detayları
            if b_t > ndl:
                st.warning("⚠️ DURUM: DEKOMPRESYONLU DALIŞ")
                deco = DiveLogic.get_deco_details(equiv_d, b_t)
                if deco and "stops" in deco:
                    st.write("**Deko Durakları ve Süreleri:**")
                    stops_data = [{"Derinlik (ft)": k, "Süre (dk)": v} for k, v in deco["stops"].items() if v > 0]
                    st.table(pd.DataFrame(stops_data))
                    group = deco["final_group"]
                else: group = "Z"
            else:
                st.info("DURUM: GÜVENLİ (NDL DAHİLİ)")
                group = DiveLogic.get_group_letter(equiv_d, b_t)

            r3.metric("Dalış Sonu Grubu", group)
            
            # Hava Analizi
            st.write("---")
            st.write("📊 **GAZ TÜKETİM ANALİZİ**")
            ata = (d_f / 33) + 1
            usage = 20 * ata * b_t
            rem = (t_v * t_p) - usage
            
            h1, h2 = st.columns(2)
            h1.write(f"Toplam Mevcut Gaz: **{t_v*t_p} Litre**")
            h1.write(f"Tahmini Tüketim: **{usage:.0f} Litre**")
            h2.progress(max(0.0, min(1.0, rem/(t_v*t_p))), text=f"Kalan Gaz: {max(0, rem):.0f} L")
            
            st.session_state['last_group'] = group

# --- TAB 2: MÜKERRER DALIŞ ---
with tab2:
    st.subheader("Mükerrer Dalış Planlama Paneli")
    
    col_rep1, col_rep2 = st.columns([1, 1.5])
    
    with col_rep1:
        current_g = st.selectbox("Önceki Dalış Grubu", list("ABCDEFGHIJKLMNOPZ"), 
                                index="ABCDEFGHIJKLMNOPZ".find(st.session_state['last_group']))
        
        si_val = st.text_input("Yüzey Aralığı (SS:DD)", value="02:00")
        next_d_m = st.number_input("2. Dalış Derinliği (Metre)", value=18.0)
        next_d_f = next_d_m * 3.28084
        next_t = st.number_input("2. Dalış Planlanan Süre (dk)", value=25)
        
        rep_btn = st.button("MÜKERRER ANALİZ YAP", use_container_width=True, type="secondary")

    with col_rep2:
        if rep_btn:
            try:
                h, m = map(int, si_val.split(':'))
                total_si = h * 60 + m
                
                # 1. SI Sonrası Yeni Grup
                new_g = DiveLogic.get_new_group_after_si(current_g, total_si)
                # 2. RNT Hesabı
                rnt = DiveLogic.calculate_rnt(next_d_f, new_g)
                total_time = rnt + next_t
                # 3. NDL Hesabı
                next_ndl = DiveLogic.get_ndl(next_d_f)
                
                st.markdown(f"### 🏁 Mükerrer Analiz Sonuçları")
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Yeni Grup", new_g)
                m2.metric("RNT (Artık Azot)", f"{rnt} dk")
                m3.metric("Toplam Hesap Zamanı", f"{total_time} dk")
                
                st.write("---")
                
                if total_time > next_ndl:
                    st.error(f"⚠️ DİKKAT: Toplam süre ({total_time} dk), NDL sınırını ({next_ndl} dk) aşıyor!")
                    st.write("**Önerilen Deko Planı:**")
                    deco_rep = DiveLogic.get_deco_details(next_d_f, total_time)
                    if deco_rep:
                        df_rep = pd.DataFrame([{"Derinlik (ft)": k, "Süre (dk)": v} for k, v in deco_rep["stops"].items() if v > 0])
                        st.table(df_rep)
                else:
                    st.success(f"✅ Güvenli: Toplam süre NDL sınırı olan {next_ndl} dk içerisinde.")
                
                # Mevzuat Tekrar Kontrol
                rep_alerts = check_egm_compliance(st.session_state.get('sys1', 'SCUBA'), next_d_m, next_d_f, "21", 4)
                for ra in rep_alerts: st.warning(ra)

            except Exception as e:
                st.error("Hatalı format! Lütfen yüzey aralığını 01:30 şeklinde girin.")