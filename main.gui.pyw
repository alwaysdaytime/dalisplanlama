import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from dive_logic import DiveLogic
from data_storage import SAFETY_RULES

class DiveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("US NAVY Rev 7 / EGM Mevzuat Planlayıcı")
        self.root.geometry("750x600") 
        
        # --- Değişkenler ---
        self.depth_m_var = tk.StringVar()
        self.depth_f_var = tk.StringVar()
        self.next_depth_m_var = tk.StringVar()
        self.next_depth_f_var = tk.StringVar()
        self.last_group_letter = "A"  
        self._lock = False 

        # --- Sekme Yapısı ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")

        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)

        self.notebook.add(self.tab1, text="İlk Dalış Planı")
        self.notebook.add(self.tab2, text="Mükerrer Dalış")

        self.setup_tab1()
        self.setup_tab2()
        
        # İzleyiciler (M/Ft Dönüşümü)
        self.depth_m_var.trace_add("write", self.update_from_meters)
        self.depth_f_var.trace_add("write", self.update_from_feet)
        self.next_depth_m_var.trace_add("write", self.update_next_from_meters)
        self.next_depth_f_var.trace_add("write", self.update_next_from_feet)

    def save_to_log(self, content, dive_type="ILK DALIS"):
        try:
            with open("dive_logs.txt", "a", encoding="utf-8") as f:
                f.write(f"\n{'#'*50}\nKAYIT TARIHI: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nDALIS TIPI: {dive_type}\n{content}\n{'#'*50}\n")
            messagebox.showinfo("Başarılı", "Rapor kaydedildi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Log hatası: {e}")

    def check_egm_compliance(self, dive_system, depth_m, depth_f, gas_o2, personnel):
        """Yönergelerdeki verilerin programa adaptasyonu"""
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
            alerts.append("ℹ️ İlk nitroks dalışı max 150 dk olabilir.")
        elif dive_system == "KDDS":
            if depth_m > 91: alerts.append("❌ KRİTİK: KDDS maksimum derinlik sınırı 91m aşıldı!")
            if depth_m > 42:
                alerts.append("⚠️ 42m üzeri için en kıdemli personelin yazılı izni gerekir.")
                alerts.append("🩺 KRİTİK: Sualtı hekimi ve tazyik odası bulundurulması zorunludur.")
            if personnel < 4: alerts.append("👥 EKİP: KDDS için en az 4 personel gereklidir.")
        return alerts

    def setup_tab1(self):
        main_frame = tk.Frame(self.tab1)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        input_frame = tk.LabelFrame(main_frame, text=" Dalış Parametreleri ", padx=10, pady=10)
        input_frame.pack(side="left", fill="y", padx=5)

        tk.Label(input_frame, text="Dalış Sistemi:", font=('Arial', 10, 'bold'), fg="blue").grid(row=0, column=0, sticky="w")
        self.combo_system = ttk.Combobox(input_frame, values=["SCUBA", "SİDS", "NİTROKS", "KDDS"], state="readonly")
        self.combo_system.set("SCUBA"); self.combo_system.grid(row=0, column=1, pady=5)

        tk.Label(input_frame, text="Personel Sayısı:").grid(row=1, column=0, sticky="w")
        self.ent_personnel = tk.Entry(input_frame); self.ent_personnel.insert(0, "4"); self.ent_personnel.grid(row=1, column=1)

        tk.Label(input_frame, text="İrtifa (Feet):").grid(row=2, column=0, sticky="w")
        self.ent_altitude = tk.Entry(input_frame); self.ent_altitude.insert(0, "0"); self.ent_altitude.grid(row=2, column=1)

        tk.Label(input_frame, text="Derinlik (m):").grid(row=3, column=0, sticky="w")
        self.ent_depth_m = tk.Entry(input_frame, textvariable=self.depth_m_var); self.ent_depth_m.grid(row=3, column=1)

        tk.Label(input_frame, text="Derinlik (ft):").grid(row=4, column=0, sticky="w")
        self.ent_depth_f = tk.Entry(input_frame, textvariable=self.depth_f_var); self.ent_depth_f.grid(row=4, column=1)

        tk.Label(input_frame, text="Dip Zamanı (dk):").grid(row=5, column=0, sticky="w")
        self.ent_time = tk.Entry(input_frame); self.ent_time.grid(row=5, column=1)

        tk.Label(input_frame, text="Gaz (%O2):").grid(row=6, column=0, sticky="w")
        self.ent_gas_type = tk.Entry(input_frame); self.ent_gas_type.insert(0, "21"); self.ent_gas_type.grid(row=6, column=1)

        # Tüp Verileri (Tab 1)
        tk.Label(input_frame, text="Tüp Hacmi (L):", fg="darkgreen").grid(row=7, column=0, sticky="w")
        self.ent_tank_vol1 = tk.Entry(input_frame); self.ent_tank_vol1.insert(0, "12"); self.ent_tank_vol1.grid(row=7, column=1)

        tk.Label(input_frame, text="Gaz Basıncı (Bar):", fg="darkgreen").grid(row=8, column=0, sticky="w")
        self.ent_gas_press1 = tk.Entry(input_frame); self.ent_gas_press1.insert(0, "200"); self.ent_gas_press1.grid(row=8, column=1)

        self.btn_calc = tk.Button(input_frame, text="HESAPLA & DENETLE", command=self.calculate_dive, bg="#003366", fg="white", font=('Arial', 10, 'bold'))
        self.btn_calc.grid(row=9, column=0, columnspan=2, pady=10, sticky="we")

        self.btn_log1 = tk.Button(input_frame, text="LOG KAYDET", command=lambda: self.save_to_log(self.txt_result.get(1.0, tk.END), "ILK DALIS"), bg="#555555", fg="white")
        self.btn_log1.grid(row=10, column=0, columnspan=2, pady=5, sticky="we")

        output_frame = tk.Frame(main_frame)
        output_frame.pack(side="right", fill="both", expand=True, padx=5)
        self.txt_result = tk.Text(output_frame, font=('Consolas', 11), bg="#f0f0f0")
        self.txt_result.pack(fill="both", expand=True)

    def calculate_dive(self):
        try:
            alt = float(self.ent_altitude.get() or 0)
            depth_f = float(self.depth_f_var.get())
            depth_m = float(self.depth_m_var.get())
            b_time = float(self.ent_time.get())
            gas_o2 = self.ent_gas_type.get()
            sys_type = self.combo_system.get()
            pers_count = int(self.ent_personnel.get() or 0)
            t_vol = float(self.ent_tank_vol1.get() or 0)
            t_press = float(self.ent_gas_press1.get() or 0)

            equiv_depth = DiveLogic.get_altitude_correction(depth_f, alt)
            ndl = DiveLogic.get_ndl(equiv_depth)
            
            self.txt_result.delete(1.0, tk.END)
            self.txt_result.insert(tk.END, f"{'='*45}\n ANALİZ VE MEVZUAT RAPORU\n{'='*45}\n\n")
            
            compliance_alerts = self.check_egm_compliance(sys_type, depth_m, depth_f, gas_o2, pers_count)
            if not compliance_alerts:
                self.txt_result.insert(tk.END, "✅ Planlanan dalış EGM yönergelerine UYGUNDUR.\n\n", "success")
            else:
                for alert in compliance_alerts: self.txt_result.insert(tk.END, f"{alert}\n", "warning")
                self.txt_result.insert(tk.END, "\n")

            self.txt_result.insert(tk.END, f"Seçilen Sistem: {sys_type}\nDerinlik: {depth_f:.1f} ft ({depth_m} m)\nNDL Sınırı: {ndl} dk\n")
            
            is_deco = b_time > ndl
            if is_deco:
                self.txt_result.insert(tk.END, "DURUM: !!! DEKOMPRESYONLU DALIŞ !!!\n", "warning")
                deco_data = DiveLogic.get_deco_details(equiv_depth, b_time)
                if deco_data:
                    for sd, dur in sorted(deco_data["stops"].items(), key=lambda x: int(x[0]), reverse=True):
                        if dur > 0: self.txt_result.insert(tk.END, f" -> {sd} ft Durağı: {dur} dk\n")
                    group = deco_data["final_group"]
                else: group = "Z"
            else:
                self.txt_result.insert(tk.END, "DURUM: GÜVENLİ (NDL DAHİLİ)\n")
                group = DiveLogic.get_group_letter(equiv_depth, b_time)

            # Hava Analizi Çıktısı
            ata = (depth_f / 33) + 1
            est_usage = 20 * ata * b_time # Ortalama 20 L/dk üzerinden
            rem_gas = (t_vol * t_press) - est_usage
            self.txt_result.insert(tk.END, f"\n--- HAVA ANALİZİ ---\n")
            self.txt_result.insert(tk.END, f"Mevcut Gaz: {t_vol * t_press:.0f} Litre\n")
            self.txt_result.insert(tk.END, f"Tahmini Tüketim: {est_usage:.0f} Litre\n")
            self.txt_result.insert(tk.END, f"Kalan Gaz: {max(0, rem_gas):.0f} Litre\n")

            self.txt_result.insert(tk.END, f"\nDalış Sonu Grup: {group}\n")
            self.last_group_letter = group
            self.lbl_current_group.config(text=group)
            self.txt_result.tag_config("warning", foreground="red", font=('Arial', 10, 'bold'))
            self.txt_result.tag_config("success", foreground="green", font=('Arial', 10, 'bold'))
        except ValueError: messagebox.showerror("Hata", "Girişleri kontrol edin.")

    def setup_tab2(self):
        main_frame = tk.Frame(self.tab2)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        input_frame = tk.LabelFrame(main_frame, text=" Mükerrer Dalış Parametreleri ", padx=10, pady=10)
        input_frame.pack(side="left", fill="y", padx=5)

        tk.Label(input_frame, text="Önceki Grup:").grid(row=0, column=0, sticky="w")
        self.lbl_current_group = tk.Label(input_frame, text=self.last_group_letter, font=('Arial', 12, 'bold'), fg="red")
        self.lbl_current_group.grid(row=0, column=1, sticky="w")

        tk.Label(input_frame, text="Yüzey Aralığı (SS:DD):").grid(row=1, column=0, sticky="w")
        self.ent_si = tk.Entry(input_frame); self.ent_si.insert(0, "01:00"); self.ent_si.grid(row=1, column=1)

        tk.Label(input_frame, text="Mükerrer Derinlik (m):").grid(row=2, column=0, sticky="w")
        self.ent_next_depth_m = tk.Entry(input_frame, textvariable=self.next_depth_m_var); self.ent_next_depth_m.grid(row=2, column=1)

        tk.Label(input_frame, text="Mükerrer Derinlik (ft):").grid(row=3, column=0, sticky="w")
        self.ent_next_depth_f = tk.Entry(input_frame, textvariable=self.next_depth_f_var); self.ent_next_depth_f.grid(row=3, column=1)

        tk.Label(input_frame, text="Dip Zamanı (dk):").grid(row=4, column=0, sticky="w")
        self.ent_next_time = tk.Entry(input_frame); self.ent_next_time.grid(row=4, column=1)

        # Tüp Verileri (Tab 2)
        tk.Label(input_frame, text="Tüp Hacmi (L):", fg="darkgreen").grid(row=5, column=0, sticky="w")
        self.ent_tank_vol2 = tk.Entry(input_frame); self.ent_tank_vol2.insert(0, "12"); self.ent_tank_vol2.grid(row=5, column=1)

        tk.Label(input_frame, text="Gaz Basıncı (Bar):", fg="darkgreen").grid(row=6, column=0, sticky="w")
        self.ent_gas_press2 = tk.Entry(input_frame); self.ent_gas_press2.insert(0, "200"); self.ent_gas_press2.grid(row=6, column=1)

        self.btn_calc_repeat = tk.Button(input_frame, text="MÜKERRER ANALİZİ YAP", command=self.calculate_repeated_dive, bg="#2E7D32", fg="white", font=('Arial', 10, 'bold'))
        self.btn_calc_repeat.grid(row=7, column=0, columnspan=2, pady=15, sticky="we")

        output_frame = tk.Frame(main_frame)
        output_frame.pack(side="right", fill="both", expand=True, padx=5)
        self.txt_result_repeat = tk.Text(output_frame, font=('Consolas', 11), bg="#f1f8e9")
        self.txt_result_repeat.pack(fill="both", expand=True)

    def calculate_repeated_dive(self):
        try:
            si_str = self.ent_si.get()
            si_min = (int(si_str.split(":")[0])*60 + int(si_str.split(":")[1])) if ":" in si_str else float(si_str)
            next_depth_f = float(self.next_depth_f_var.get())
            next_time = float(self.ent_next_time.get() or 0)
            t_vol = float(self.ent_tank_vol2.get() or 0)
            t_press = float(self.ent_gas_press2.get() or 0)
            
            new_group = DiveLogic.get_new_group_after_si(self.last_group_letter, si_min)
            rnt = DiveLogic.calculate_rnt(next_depth_f, new_group)
            total_time = rnt + next_time
            
            self.txt_result_repeat.delete(1.0, tk.END)
            self.txt_result_repeat.insert(tk.END, f"{'='*40}\n MÜKERRER DALIŞ SONUCU\n{'='*40}\n\n")
            self.txt_result_repeat.insert(tk.END, f"SI Sonrası Grup: {new_group}\nArtık Azot Zamanı (RNT): {rnt} dk\n")
            self.txt_result_repeat.insert(tk.END, f"Planlanan Dip Zamanı: {next_time} dk\n")
            self.txt_result_repeat.insert(tk.END, f"TOPLAM HESAP ZAMANI: {total_time} dk\n")

            # Mükerrer Hava Analizi
            ata = (next_depth_f / 33) + 1
            est_usage = 20 * ata * next_time
            self.txt_result_repeat.insert(tk.END, f"\n--- HAVA ANALİZİ ---\n")
            self.txt_result_repeat.insert(tk.END, f"Mevcut Gaz: {t_vol * t_press:.0f} L\n")
            self.txt_result_repeat.insert(tk.END, f"Tahmini Tüketim: {est_usage:.0f} L\n")
            self.txt_result_repeat.insert(tk.END, f"Kalan Gaz: {max(0, (t_vol*t_press)-est_usage):.0f} L\n")

            alerts = self.check_egm_compliance(self.combo_system.get(), next_depth_f/3.28, next_depth_f, 21, int(self.ent_personnel.get() or 0))
            for alert in alerts: self.txt_result_repeat.insert(tk.END, f"\n{alert}", "warning")
            self.txt_result_repeat.tag_config("warning", foreground="red")
        except Exception as e: messagebox.showerror("Hata", f"Hata: {e}")

    def _update_conversions(self, source_var, target_var, factor, is_multiply):
        if not self._lock:
            self._lock = True
            try:
                val = float(source_var.get())
                res = val * factor if is_multiply else val / factor
                target_var.set(f"{round(res, 1)}")
            except: target_var.set("")
            self._lock = False

    def update_from_meters(self, *args): self._update_conversions(self.depth_m_var, self.depth_f_var, 3.28084, True)
    def update_from_feet(self, *args): self._update_conversions(self.depth_f_var, self.depth_m_var, 3.28084, False)
    def update_next_from_meters(self, *args): self._update_conversions(self.next_depth_m_var, self.next_depth_f_var, 3.28084, True)
    def update_next_from_feet(self, *args): self._update_conversions(self.next_depth_f_var, self.next_depth_m_var, 3.28084, False)

if __name__ == "__main__":
    root = tk.Tk()
    app = DiveApp(root)
    root.mainloop()