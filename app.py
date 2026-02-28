import streamlit as st
from datetime import datetime
from dive_logic import DiveLogic  # Hesaplama mantığınız
import pandas as pd

# Sayfa Genişlik ve Başlık Ayarı
st.set_page_config(page_title="US NAVY Rev 7 / EGM Mevzuat Planlayıcı", layout="wide", page_icon="🌊")

# --- CSS ile Arayüzü Güzelleştirme ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_stdio=True)

def check_egm_compliance(dive_system, depth_m, depth_f, gas_o2, personnel):
    """EGM Mevzuat Denetimi"""
    alerts = []
    if dive_system == "SCUBA":
        if depth_f > 140: alerts.append("❌ KRİTİK: Scuba ile maksimum derinlik sınırı 140 ft (42m) aşılamaz!")
        if personnel < 3: alerts.append("👥 EKİP: Scuba dalışlarında en az 3 personel bulunmalıdır.")
    elif dive_system == "SİDS":
        if depth_f > 190: alerts.append("❌ KRİTİK: SİDS maksimum derinlik sınırı 190 ft (58m) aşıldı!")
        elif depth_f > 140: alerts.append("⚠️ UYARI: 140 ft üzeri için en rütbeli kurbağa adamın yazılı izni şarttır.")
        if personnel < 4: alerts.append("👥 EKİP: 10m altı için dahi en az 4 personel gereklidir.")
        if depth_f > 33 and personnel < 7: alerts.append("👥 EKİP: 10m üzeri derinlikte ekip en az 7 kişi olmalıdır.")
    elif dive_system == "NİTROKS":
        try:
            o2 = int(gas_o2)
            if o2 == 32 and depth_m > 33: alerts.append("❌ MEVZUAT: %32 Nitroks için derinlik sınırı 33 metredir.")
            if o2 == 36 and depth_m > 28: alerts.append("❌ MEVZUAT: %36 Nitroks için derinlik sınırı 28 metredir.")
        except: pass
    elif dive_system == "KDDS":
        if depth_m > 91: alerts.append("❌ KRİTİK: KDDS maksimum derinlik sınırı 91m aşıldı!")
        if depth_m > 42:
            alerts.append("⚠️ 42m üzeri için en kıdemli personelin yazılı izni gerekir.")
            alerts.append("🩺 KRİTİK: Sualtı hekimi ve tazyik odası bulundurulması zorunludur.")
        if personnel < 4: alerts.append("👥 EKİP: KDDS için en az 4 personel gereklidir.")
    return alerts

st.title("🌊 US NAVY Rev 7 / EGM Mevzuat Planlayıcı")
st.divider()

tab1, tab2 = st.tabs(["📋 İlk Dalış Planı", "🔄 Mükerrer Dalış"])

with tab1:
    col_in, col_out = st.columns([1, 1.5])
    
    with col_in:
        st.subheader("Dalış Parametreleri")
        sys_type = st.selectbox("Dalış Sistemi", ["SCUBA", "SİDS", "NİTROKS", "KDDS"], index=0)
        pers_count = st.number_input("Personel Sayısı", min_value=1, value=4)
        alt = st.number_input("İrtifa (Feet)", value=0, step=500)
        
        d_m = st.number_input("Derinlik (Metre)", value=20.0, step=0.5)
        d_f = d_m * 3.28084
        st.caption(f"Hesaplanan Derinlik: {d_f:.1f} ft")
        
        b_t = st.number_input("Dip Zamanı (Dakika)", value=30, step=1)
        g_o2 = st.text_input("Gaz (%O2)", value="21")
        
        st.write("---")
        st.write("🟢 **Tüp Verileri**")
        t_v = st.number_input("Tüp Hacmi (L)", value=12)
        t_p = st.number_input("Gaz Basıncı (Bar)", value=200)
        
        calc_btn = st.button("ANALİZİ BAŞLAT", use_container_width=True, type="primary")

    with col_out:
        st.subheader("Analiz ve Mevzuat Raporu")
        if calc_btn:
            # 1. Mevzuat Kontrolü
            compliance_alerts = check_egm_compliance(sys_type, d_m, d_f, g_o2, pers_count)
            if not compliance_alerts:
                st.success("✅ Planlanan dalış EGM yönergelerine UYGUNDUR.")
            else:
                for alert in compliance_alerts:
                    st.error(alert)

            # 2. Deko ve NDL Analizi
            equiv_depth = DiveLogic.get_altitude_correction(d_f, alt)
            ndl = DiveLogic.get_ndl(equiv_depth)
            
            st.info(f"**NDL Sınırı:** {ndl} dk | **Eşdeğer Derinlik:** {equiv_depth:.1f} ft")
            
            if b_t > ndl:
                st.warning("⚠️ DURUM: DEKOMPRESYONLU DALIŞ!")
                deco_data = DiveLogic.get_deco_details(equiv_depth, b_t)
                if deco_data:
                    st.write("**Deko Durakları:**")
                    # Durakları tablo olarak göster
                    stops_list = []
                    for sd, dur in sorted(deco_data["stops"].items(), key=lambda x: int(x[0]), reverse=True):
                        if dur > 0:
                            stops_list.append({"Durak Derinliği (ft)": sd, "Bekleme Süresi (dk)": dur})
                    st.table(pd.DataFrame(stops_list))
                    group = deco_data["final_group"]
                else:
                    st.error("Deko verisi hesaplanamadı (Tablo dışı değer).")
                    group = "Z"
            else:
                st.success("DURUM: GÜVENLİ (NDL DAHİLİ)")
                group = DiveLogic.get_group_letter(equiv_depth, b_t)
            
            # 3. Hava Analizi
            ata = (d_f / 33) + 1
            est_usage = 20 * ata * b_t
            rem_gas = (t_v * t_p) - est_usage
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Mevcut Gaz", f"{t_v*t_p} L")
            c2.metric("Tahmini Tüketim", f"{est_usage:.0f} L", delta=f"-{est_usage:.0f}", delta_color="inverse")
            c3.metric("Kalan Gaz", f"{max(0, rem_gas):.0f} L")

            st.subheader(f"Dalış Sonu Grup: :red[{group}]")
            st.session_state['last_group'] = group
            st.session_state['last_sys'] = sys_type

with tab2:
    st.subheader("Mükerrer Dalış Analizi")
    current_group = st.session_state.get('last_group', 'A')
    
    col_rep_in, col_rep_out = st.columns([1, 1.5])
    
    with col_rep_in:
        st.write(f"Önceki Dalış Sonu Grup: **{current_group}**")
        si_str = st.text_input("Yüzey Aralığı (SS:DD)", value="01:00")
        n_d_m = st.number_input("Mükerrer Derinlik (Metre)", value=15.0)
        n_t = st.number_input("Mükerrer Dip Zamanı (Dakika)", value=20)
        
        rep_calc_btn = st.button("MÜKERRER HESAPLA", use_container_width=True)

    with col_rep_out:
        if rep_calc_btn:
            try:
                h, m = map(int, si_str.split(':'))
                si_min = h * 60 + m
                n_d_f = n_d_m * 3.28084
                
                new_group = DiveLogic.get_new_group_after_si(current_group, si_min)
                rnt = DiveLogic.calculate_rnt(n_d_f, new_group)
                total_t = rnt + n_t
                
                st.write(f"**Yüzey Aralığı Sonrası Grup:** {new_group}")
                st.write(f"**Artık Azot Zamanı (RNT):** {rnt} dk")
                st.info(f"**Toplam Hesap Zamanı:** {total_t} dk")
                
                # Mükerrer Deko/NDL
                ndl_rep = DiveLogic.get_ndl(n_d_f)
                if total_t > ndl_rep:
                    st.warning("⚠️ MÜKERRER DALIŞ DEKOMPRESYON GEREKTİRİR!")
                    # Buraya tab1'deki deko detaylarını getiren mantığı ekleyebilirsiniz
                else:
                    st.success("Mükerrer dalış NDL dahilinde.")
                
                # Mevzuat uyarısı (Mükerrer için)
                rep_alerts = check_egm_compliance(st.session_state.get('last_sys', 'SCUBA'), n_d_m, n_d_f, "21", 4)
                for ra in rep_alerts: st.warning(ra)
                
            except Exception as e:
                st.error(f"Hata: {e}. Lütfen SS:DD formatında girin.")
