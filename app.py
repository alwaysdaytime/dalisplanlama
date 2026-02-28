import streamlit as st
import pandas as pd
from datetime import datetime

# Hata ayıklama için DiveLogic içe aktarımı
try:
    from dive_logic import DiveLogic
except ImportError:
    st.error("HATA: 'dive_logic.py' dosyası GitHub deposunda bulunamadı!")

st.set_page_config(page_title="EGM Dalış Planlayıcı", layout="wide", page_icon="🌊")

def check_egm_compliance(dive_system, depth_m, depth_f, gas_o2, personnel):
    alerts = []
    if dive_system == "SCUBA":
        if depth_f > 140: alerts.append("❌ KRİTİK: Scuba ile 140 ft (42m) sınırı aşılamaz!")
        if personnel < 3: alerts.append("👥 EKİP: En az 3 personel bulunmalıdır.")
    elif dive_system == "SİDS":
        if depth_f > 190: alerts.append("❌ KRİTİK: SİDS 190 ft (58m) sınırı aşıldı!")
        if personnel < 4: alerts.append("👥 EKİP: En az 4 personel gereklidir.")
    elif dive_system == "NİTROKS":
        try:
            o2 = int(gas_o2)
            if o2 == 32 and depth_m > 33: alerts.append("❌ MEVZUAT: %32 Nitroks sınırı 33m.")
            if o2 == 36 and depth_m > 28: alerts.append("❌ MEVZUAT: %36 Nitroks sınırı 28m.")
        except: pass
    return alerts

st.title("🌊 US NAVY Rev 7 / EGM Mevzuat Planlayıcı")

tab1, tab2 = st.tabs(["📋 İlk Dalış", "🔄 Mükerrer Dalış"])

with tab1:
    c1, c2 = st.columns([1, 1.5])
    with c1:
        sys_type = st.selectbox("Sistem", ["SCUBA", "SİDS", "NİTROKS", "KDDS"])
        depth_m = st.number_input("Derinlik (Metre)", value=20.0)
        depth_f = depth_m * 3.28084
        b_time = st.number_input("Dip Zamanı (Dakika)", value=30)
        pers = st.number_input("Personel", value=4)
        gas = st.text_input("Gaz %O2", value="21")
        
        st.write("---")
        t_v = st.number_input("Tüp (L)", value=12)
        t_p = st.number_input("Basınç (Bar)", value=200)
        
        btn = st.button("HESAPLA", type="primary", use_container_width=True)

    with c2:
        if btn:
            # Mevzuat
            alerts = check_egm_compliance(sys_type, depth_m, depth_f, gas, pers)
            for a in alerts: st.error(a)
            if not alerts: st.success("✅ Mevzuata Uygun")

            # Hesaplamalar
            ndl = DiveLogic.get_ndl(depth_f)
            st.metric("NDL Sınırı", f"{ndl} dk")

            if b_time > ndl:
                st.warning("⚠️ DEKOMPRESYON GEREKLİ")
                deco = DiveLogic.get_deco_details(depth_f, b_time)
                if deco and "stops" in deco:
                    df_stops = pd.DataFrame([{"Derinlik (ft)": k, "Süre (dk)": v} for k, v in deco["stops"].items() if v > 0])
                    st.table(df_stops)
                    group = deco["final_group"]
                else: group = "Z"
            else:
                group = DiveLogic.get_group_letter(depth_f, b_time)
            
            st.subheader(f"Dalış Sonu Grup: {group}")
            st.session_state['last_group'] = group

# Mükerrer dalış sekmesi aynı mantıkla devam eder...