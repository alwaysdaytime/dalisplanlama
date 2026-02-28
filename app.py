import streamlit as st
from datetime import datetime
from dive_logic import DiveLogic  # Mevcut mantık dosyanız

# Sayfa Ayarları
st.set_page_config(page_title="US NAVY Rev 7 / EGM Planlayıcı", layout="wide")

def check_egm_compliance(dive_system, depth_m, depth_f, gas_o2, personnel):
    alerts = []
    if dive_system == "SCUBA":
        if depth_f > 140: alerts.append("❌ KRİTİK: Scuba ile 140 ft (42m) sınırı aşılamaz!")
        if personnel < 3: alerts.append("👥 EKİP: En az 3 personel bulunmalıdır.")
    elif dive_system == "SİDS":
        if depth_f > 190: alerts.append("❌ KRİTİK: SİDS 190 ft (58m) sınırı aşıldı!")
        if personnel < 4: alerts.append("👥 EKİP: En az 4 personel gereklidir.")
        if depth_f > 33 and personnel < 7: alerts.append("👥 EKİP: 10m üzeri için ekip en az 7 kişi olmalıdır.")
    elif dive_system == "NİTROKS":
        try:
            o2 = int(gas_o2)
            if o2 == 32 and depth_m > 33: alerts.append("❌ MEVZUAT: %32 Nitroks sınırı 33 metredir.")
            if o2 == 36 and depth_m > 28: alerts.append("❌ MEVZUAT: %36 Nitroks sınırı 28 metredir.")
        except: pass
    return alerts

st.title("🌊 US NAVY Rev 7 / EGM Mevzuat Planlayıcı")

# Sekmeler
tab1, tab2 = st.tabs(["İlk Dalış Planı", "Mükerrer Dalış"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Parametreler")
        sys_type = st.selectbox("Dalış Sistemi", ["SCUBA", "SİDS", "NİTROKS", "KDDS"])
        pers_count = st.number_input("Personel Sayısı", min_value=1, value=4)
        alt = st.number_input("İrtifa (Feet)", value=0)
        
        # Derinlik Girişleri
        depth_m = st.number_input("Derinlik (Metre)", value=0.0, step=0.1)
        depth_f = depth_m * 3.28084
        st.caption(f"Eşdeğer Derinlik: {depth_f:.1f} Feet")
        
        b_time = st.number_input("Dip Zamanı (Dakika)", value=0)
        gas_o2 = st.text_input("Gaz (%O2)", value="21")
        
        t_vol = st.number_input("Tüp Hacmi (Litre)", value=12)
        t_press = st.number_input("Gaz Basıncı (Bar)", value=200)

    with col2:
        st.subheader("Analiz Raporu")
        if st.button("HESAPLA VE DENETLE"):
            equiv_depth = DiveLogic.get_altitude_correction(depth_f, alt)
            ndl = DiveLogic.get_ndl(equiv_depth)
            
            # Mevzuat Denetimi
            alerts = check_egm_compliance(sys_type, depth_m, depth_f, gas_o2, pers_count)
            if not alerts:
                st.success("✅ Planlanan dalış EGM yönergelerine UYGUNDUR.")
            else:
                for a in alerts: st.error(a)
            
            # Deko Kontrolü
            if b_time > ndl:
                st.warning("⚠️ DURUM: DEKOMPRESYONLU DALIŞ!")
                deco_data = DiveLogic.get_deco_details(equiv_depth, b_time)
                if deco_data:
                    for sd, dur in sorted(deco_data["stops"].items(), key=lambda x: int(x[0]), reverse=True):
                        if dur > 0: st.info(f"📍 {sd} ft Durağı: {dur} dk")
                    group = deco_data["final_group"]
                else: group = "Z"
            else:
                st.info(f"DURUM: GÜVENLİ (NDL: {ndl} dk)")
                group = DiveLogic.get_group_letter(equiv_depth, b_time)
            
            # Hava Analizi
            ata = (depth_f / 33) + 1
            est_usage = 20 * ata * b_time
            st.metric("Tahmini Tüketim", f"{est_usage:.0f} L")
            st.metric("Kalan Gaz", f"{max(0, (t_vol*t_press)-est_usage):.0f} L")
            st.subheader(f"Dalış Sonu Grup: {group}")
            st.session_state['last_group'] = group

with tab2:
    st.subheader("Mükerrer Dalış Analizi")
    prev_group = st.session_state.get('last_group', 'A')
    st.write(f"Önceki Dalış Grubu: **{prev_group}**")
    
    si_input = st.text_input("Yüzey Aralığı (Örn: 01:30)", value="01:00")
    next_depth_m = st.number_input("Mükerrer Derinlik (Metre)", value=0.0, key="ndm")
    next_time = st.number_input("Planlanan Dip Zamanı (dk)", value=0, key="nt")
    
    if st.button("MÜKERRER HESAPLA"):
        try:
            h, m = map(int, si_input.split(':'))
            si_min = h * 60 + m
            next_depth_f = next_depth_m * 3.28084
            
            new_group = DiveLogic.get_new_group_after_si(prev_group, si_min)
            rnt = DiveLogic.calculate_rnt(next_depth_f, new_group)
            total_time = rnt + next_time
            
            st.write(f"SI Sonrası Grup: **{new_group}**")
            st.write(f"Artık Azot Zamanı (RNT): **{rnt} dk**")
            st.write(f"Toplam Hesap Zamanı: **{total_time} dk**")
            
            # Mükerrer Deko Kontrolü
            ndl_next = DiveLogic.get_ndl(next_depth_f)
            if total_time > ndl_next:
                st.error("⚠️ BU DALIŞ DEKOMPRESYON GEREKTİRİR!")
        except:
            st.error("Giriş formatını kontrol edin.")