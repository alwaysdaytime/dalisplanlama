import math
from data_storage import (
    USN_REV7_DATA, SURFACE_INTERVAL_DATA, RNT_DATA, 
    AIR_DECO_DATA, ALTITUDE_CORRECTION, SAFETY_RULES
)

class DiveLogic:
    @staticmethod
    def get_altitude_correction(depth_feet, altitude_feet):
        """
        Tablo 9-4 ve 9-5'e göre irtifa düzeltmesi yapar.
        Gerçek derinliği, deniz seviyesi eşdeğeri olan 'Equivalent Depth'e çevirir.
        """
        if altitude_feet <= 0:
            return depth_feet
        
        # Mevcut irtifadan büyük veya eşit olan en yakın irtifa basamağını bulur
        sorted_altitudes = sorted(ALTITUDE_CORRECTION.keys())
        target_alt = next((alt for alt in sorted_altitudes if altitude_feet <= alt), sorted_altitudes[-1])
        
        factor = ALTITUDE_CORRECTION.get(target_alt, 1.0)
        return depth_feet * factor

    @staticmethod
    def get_ndl(depth_feet):
        """
        Tablo 9-7'ye göre verilen derinlik için Sıfır Dekompresyon Limitini (NDL) döner.
        """
        depth_list = sorted(USN_REV7_DATA.keys())
        # Derinliği bir üst standart değere yuvarlar (Örn: 42 ft -> 45 ft tablosu)
        target_depth = next((d for d in depth_list if d >= depth_feet), None)
        
        if target_depth:
            return USN_REV7_DATA[target_depth]["ndl"]
        return 0

    @staticmethod
    def get_deco_details(depth_feet, bottom_time):
        """
        Tablo 9-9 (Hava Dekompresyon Tablosu) verilerini sorgular.
        Eğer dalış NDL'i aşmışsa gereken durakları ve final grup harfini döner.
        """
        depth_list = sorted(AIR_DECO_DATA.keys())
        target_depth = next((d for d in depth_list if d >= depth_feet), None)
        
        if target_depth and target_depth in AIR_DECO_DATA:
            times = sorted(AIR_DECO_DATA[target_depth].keys())
            # Dip zamanını bir üst tablo değerine yuvarlar
            target_time = next((t for t in times if t >= bottom_time), None)
            
            if target_time:
                return AIR_DECO_DATA[target_depth][target_time]
        return None

    @staticmethod
    def get_group_letter(depth_feet, bottom_time):
        """
        Tablo 9-7'ye göre dekompresyonsuz dalış sonrası grup harfini belirler.
        """
        depth_list = sorted(USN_REV7_DATA.keys())
        target_depth = next((d for d in depth_list if d >= depth_feet), None)
        
        if target_depth:
            for start, end, letter in USN_REV7_DATA[target_depth]["groups"]:
                if start <= bottom_time <= end:
                    return letter
        return 'Z' # Tablo dışı veya aşırı limit durumunda en riskli grup

    @staticmethod
    def get_new_group_after_si(old_group, interval_minutes):
        """
        Tablo 9-8 (Üst) Satıh fasılası sonrası yeni grup harfini hesaplar.
        """
        if old_group not in SURFACE_INTERVAL_DATA:
            return old_group
            
        for start_str, end_str, new_letter in SURFACE_INTERVAL_DATA[old_group]:
            h1, m1 = map(int, start_str.split(':'))
            h2, m2 = map(int, end_str.split(':'))
            # Zaman aralığını dakika cinsinden kontrol eder
            if (h1 * 60 + m1) <= interval_minutes <= (h2 * 60 + m2):
                return new_letter
        return 'A' # Fasıla çok uzunsa vücut tamamen temizlenmiş kabul edilir

    @staticmethod
    def calculate_rnt(depth_feet, group_letter):
        """
        Tablo 9-8 (Alt) Rezidüel Nitrojen Zamanını (RNT) bulur.
        """
        if group_letter in RNT_DATA:
            depth_list = sorted(RNT_DATA[group_letter].keys())
            target_depth = next((d for d in depth_list if d >= depth_feet), None)
            if target_depth:
                return RNT_DATA[group_letter][target_depth]
        return 0

    @staticmethod
    def get_no_fly_time(is_deco_dive):
        """
        SAFETY_RULES içindeki uçuş yasak sürelerini döner.
        """
        if is_deco_dive:
            return SAFETY_RULES["FLYING_AFTER_DIVING"]["DECO"]
        return SAFETY_RULES["FLYING_AFTER_DIVING"]["NO_DECO"]