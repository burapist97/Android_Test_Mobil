import sys
import subprocess
import os

# ==========================================
#   OTOMATİK KÜTÜPHANE YÜKLEYİCİ (BAŞLANGIÇ)
# ==========================================
def bagimliliklari_kontrol_et_ve_yukle():
    gerekli_kutuphaneler = {
        "customtkinter": "customtkinter",
        "pynput": "pynput",
        "PIL": "pillow",
        "cv2": "opencv-python",
        "numpy": "numpy"
    }
    
    eksikler = []
    for modul_adi, pip_adi in gerekli_kutuphaneler.items():
        try:
            if modul_adi == "cv2":
                __import__("cv2")
            else:
                __import__(modul_adi)
        except ImportError:
            eksikler.append(pip_adi)
            
    if eksikler:
        print(f"\n[SİSTEM] Eksik kütüphaneler tespit edildi, otomatik yükleniyor: {eksikler}")
        print("-" * 50)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *eksikler])
            print("-" * 50)
            print("[SİSTEM] Tüm kütüphaneler başarıyla yüklendi! Uygulama başlatılıyor...\n")
        except Exception as e:
            print(f"\n❌ Kütüphaneler yüklenirken kritik bir hata oluştu: {e}")
            input("Çıkmak için ENTER tuşuna basın...")
            sys.exit(1)

bagimliliklari_kontrol_et_ve_yukle()

# ==========================================
#         GEREKLİ KÜTÜPHANELER
# ==========================================
import customtkinter as ctk
import threading
import time
import sqlite3
import json
import zipfile
import cv2
import numpy as np
import re
from tkinter import filedialog, messagebox
from datetime import datetime
from pynput.keyboard import Listener, Key
from PIL import Image, ImageTk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class TestOtomasyonApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Token Finansal Teknolojiler - Test Otomasyon Merkezi")
        self.geometry("1050x700")
        
        # --- DOSYA VE KLASÖR YOLLARI ---
        self.ana_dizin = os.path.dirname(os.path.abspath(__file__))
        self.db_yolu = os.path.join(self.ana_dizin, "test_merkezi.db")
        self.adb_yolu = os.path.join(self.ana_dizin, "platform-tools", "adb.exe")
        
        self.hata_klasoru = os.path.join(self.ana_dizin, "hata_gorselleri")
        os.makedirs(self.hata_klasoru, exist_ok=True) 

        self.log_klasoru = os.path.join(self.ana_dizin, "test_loglari")
        os.makedirs(self.log_klasoru, exist_ok=True)
        
        self.referans_klasoru = os.path.join(self.ana_dizin, "referans_gorseller")
        os.makedirs(self.referans_klasoru, exist_ok=True)

        # --- KAYIT MOTORU DEĞİŞKENLERİ ---
        self.kayit_aktif = False
        self.gecici_dokunuslar = []
        self.son_dokunus_zamani = 0 
        self.klavye_dinleyici = None
        self.getevent_proc = None
        self.adim_sayaci = 1
        
        # --- DONANIM VE EKRAN DEĞİŞKENLERİ ---
        self.ekran_genislik = 1080
        self.ekran_yukseklik = 1920
        self.donanim_genislik = 32767
        self.donanim_yukseklik = 32767
        self.touch_device_node = "" 

        self.cihaz_cozunurlugunu_al()
        self.veritabanini_hazirla()

        # --- GRID DÜZENİ ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SOL PANEL (MENÜ) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="TEST PANELİ", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=20, padx=10)

        self.btn_kayit_ekran = ctk.CTkButton(self.sidebar_frame, text="Yeni Kayıt Oluştur", command=self.goster_kayit)
        self.btn_kayit_ekran.pack(pady=10, padx=20)

        self.btn_liste_ekran = ctk.CTkButton(self.sidebar_frame, text="Testleri Yönet & Çalıştır", command=self.goster_liste)
        self.btn_liste_ekran.pack(pady=10, padx=20)

        self.btn_rapor_ekran = ctk.CTkButton(self.sidebar_frame, text="📊 Test Raporları", fg_color="#F4A460", text_color="black", hover_color="#d68b49", command=self.goster_raporlar)
        self.btn_rapor_ekran.pack(pady=10, padx=20)

        # --- SAĞ PANEL (İÇERİK) ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.baslangic_ekrani()

    def cihaz_cozunurlugunu_al(self):
        try:
            c_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            
            sonuc = subprocess.run([self.adb_yolu, "shell", "wm", "size"], capture_output=True, text=True, creationflags=c_flags)
            match = re.search(r"Override size:\s*(\d+)x(\d+)", sonuc.stdout)
            if not match: match = re.search(r"Physical size:\s*(\d+)x(\d+)", sonuc.stdout)
            if match:
                self.ekran_genislik = int(match.group(1))
                self.ekran_yukseklik = int(match.group(2))
                
            getevent_p = subprocess.run([self.adb_yolu, "shell", "getevent", "-p"], capture_output=True, text=True, creationflags=c_flags)
            
            aktif_cihaz = ""
            gecici_max_x, gecici_max_y = 0, 0
            
            for line in getevent_p.stdout.split('\n'):
                dev_match = re.search(r"add device \d+: (/.+)", line)
                if dev_match:
                    aktif_cihaz = dev_match.group(1).strip()
                    gecici_max_x, gecici_max_y = 0, 0 
                    
                if "0035" in line or "ABS_MT_POSITION_X" in line:
                    m = re.search(r"max\s+(\d+)", line)
                    if m: gecici_max_x = int(m.group(1))
                        
                if "0036" in line or "ABS_MT_POSITION_Y" in line:
                    m = re.search(r"max\s+(\d+)", line)
                    if m: 
                        gecici_max_y = int(m.group(1))
                        if gecici_max_y > 1000 and aktif_cihaz:
                            self.donanim_genislik = gecici_max_x
                            self.donanim_yukseklik = gecici_max_y
                            self.touch_device_node = aktif_cihaz
                            break 
                        
        except Exception:
            pass

        if self.donanim_genislik <= 0: self.donanim_genislik = self.ekran_genislik
        if self.donanim_yukseklik <= 0: self.donanim_yukseklik = self.ekran_yukseklik

    def veritabanini_hazirla(self):
        conn = sqlite3.connect(self.db_yolu)
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS case_bazli_testler (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ana_test_adi TEXT, yetkili TEXT, uygulama TEXT, amac TEXT,
            case_adi TEXT, aksiyonlar TEXT, beklenen_xml TEXT)""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS test_sonuclari (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ana_test_adi TEXT, tarih TEXT,
            toplam_adim INTEGER, basarili_adim INTEGER, genel_durum TEXT)""")
        try: cursor.execute("ALTER TABLE test_sonuclari ADD COLUMN detaylar TEXT")
        except sqlite3.OperationalError: pass 
        conn.commit()
        conn.close()

    def temizle(self):
        self.kaydi_bitir_islem()
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def baslangic_ekrani(self):
        self.temizle()
        try: aktif_kullanici = os.getlogin().capitalize()
        except: aktif_kullanici = "Kullanıcı"
        lbl = ctk.CTkLabel(self.main_frame, text=f"Token Test Otomasyonuna Hoş Geldiniz, {aktif_kullanici}!\nSoldan bir işlem seçerek başlayabilirsiniz.", font=("Arial", 16))
        lbl.pack(expand=True)

    # ==========================================
    #             1. DAHİLİ KAYIT MOTORU 
    # ==========================================
    def goster_kayit(self):
        self.temizle()
        ctk.CTkLabel(self.main_frame, text="📝 Yeni Senaryo Kaydı", font=("Arial", 18, "bold")).pack(pady=10)
        self.entry_ad = ctk.CTkEntry(self.main_frame, placeholder_text="Senaryo Adı (Örn: Login)", width=300)
        self.entry_ad.pack(pady=5)
        self.entry_yetkili = ctk.CTkEntry(self.main_frame, placeholder_text="Yetkili Kişi", width=300)
        self.entry_yetkili.pack(pady=5)
        self.entry_uygulama = ctk.CTkEntry(self.main_frame, placeholder_text="Uygulama Adı", width=300)
        self.entry_uygulama.pack(pady=5)

        self.buton_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.buton_frame.pack(pady=15)
        self.btn_baslat = ctk.CTkButton(self.buton_frame, text="KAYDI BAŞLAT", fg_color="green", hover_color="darkgreen", command=self.kaydi_tetikle)
        self.btn_baslat.grid(row=0, column=0, padx=5)
        
        # ARTIK MANUEL BUTON YOK: Otomatik durum takipçisi var
        self.lbl_oto_durum = ctk.CTkLabel(self.buton_frame, text="Zeka Bekliyor", fg_color="gray", text_color="white", corner_radius=5, width=180)
        self.lbl_oto_durum.grid(row=0, column=1, padx=5, ipadx=10, ipady=5)
        
        self.btn_bitir = ctk.CTkButton(self.buton_frame, text="Kaydı Bitir (ESC)", fg_color="red", state="disabled", command=self.kaydi_bitir_islem)
        self.btn_bitir.grid(row=0, column=2, padx=5)

        self.log_kutusu = ctk.CTkTextbox(self.main_frame, width=600, height=300)
        self.log_kutusu.pack(pady=10)
        self.log_kutusu.insert("0.0", "Sistem hazır. Bilgileri girip kaydı başlatabilirsiniz...\n")

    def kaydi_tetikle(self):
        self.guncel_test_adi = self.entry_ad.get()
        self.guncel_yetkili = self.entry_yetkili.get()
        self.guncel_uygulama = self.entry_uygulama.get()
        self.guncel_amac = "Arayüz üzerinden test"

        if not self.guncel_test_adi:
            self.log_yaz("\n❌ Hata: Senaryo adı boş olamaz!")
            return

        self.cihaz_cozunurlugunu_al()

        self.btn_baslat.configure(state="disabled")
        self.lbl_oto_durum.configure(text="Akıllı Yakalama Aktif", fg_color="#F4A460", text_color="black")
        self.btn_bitir.configure(state="normal")
        
        self.kayit_aktif = True
        self.gecici_dokunuslar = []
        self.son_dokunus_zamani = 0 
        self.adim_sayaci = 1

        self.log_yaz(f"\n🚀 '{self.guncel_test_adi}' için kayıt aktif!")
        self.log_yaz(f"🎯 Hedef Sensör Sınırı: {self.donanim_genislik}x{self.donanim_yukseklik} ({self.touch_device_node})")
        self.log_yaz("👉 Cihazda serbestçe gezinin. Siz duraksadığınız her 1.5 saniyede sistem adımı otomatik kaydeder.\n👉 Tüm test bittiğinde bilgisayardan ESC tuşuna basın.\n")

        # Hem Cihaz dinleyicisi hem de Akıllı Adım (Zamanlayıcı) motoru başlıyor
        threading.Thread(target=self.adb_getevent_dinle, daemon=True).start()
        threading.Thread(target=self.otomatik_adim_izleyici, daemon=True).start()
        
        if self.klavye_dinleyici: self.klavye_dinleyici.stop()
        self.klavye_dinleyici = Listener(on_press=self.klavye_dinle)
        self.klavye_dinleyici.start()

    def klavye_dinle(self, key):
        if not self.kayit_aktif: return 
        # SADECE ÇIKIŞ YAPMAK İÇİN ESC KALDI (ENTER IPTAL EDİLDİ)
        if key == Key.esc: self.after(0, self.kaydi_bitir_islem)

    # --- AKILLI ADIM EKLEME MOTORU (ÇARPIŞMAYI ÖNLER) ---
    def otomatik_adim_izleyici(self):
        islem_yapiliyor = False
        while self.kayit_aktif:
            time.sleep(0.3)
            if not self.kayit_aktif: break
            
            # Eğer son dokunuştan itibaren 1.5 saniye geçtiyse (kullanıcı duraksadıysa)
            if self.gecici_dokunuslar and self.son_dokunus_zamani > 0 and not islem_yapiliyor:
                gecen_sure = time.time() - self.son_dokunus_zamani
                
                if gecen_sure >= 1.5:
                    islem_yapiliyor = True
                    kopya = list(self.gecici_dokunuslar)
                    self.gecici_dokunuslar.clear()
                    
                    case_adi = f"Adim_{self.adim_sayaci}"
                    self.adim_sayaci += 1
                    
                    self.log_yaz(f"\n⏳ Otomatik Adım Yakalandı: '{case_adi}'. Ekran Çekiliyor...")
                    self.arka_planda_case_kaydet(case_adi, kopya)
                    islem_yapiliyor = False

    def adb_getevent_dinle(self):
        c_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        cmd = [self.adb_yolu, "shell", "getevent", "-lt"]
        if self.touch_device_node: cmd.append(self.touch_device_node)
        self.getevent_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', bufsize=1, creationflags=c_flags)
        
        slots = {}
        current_slot = 0
        cihaz_mt_destekli = False
        
        def process_touch(slot_data):
            if slot_data.get('start_x') is None or slot_data.get('start_y') is None: return
            if slot_data.get('end_x') is None or slot_data.get('end_y') is None: return
            
            sx = int((slot_data['start_x'] / max(1, self.donanim_genislik)) * self.ekran_genislik)
            sy = int((slot_data['start_y'] / max(1, self.donanim_yukseklik)) * self.ekran_yukseklik)
            ex = int((slot_data['end_x'] / max(1, self.donanim_genislik)) * self.ekran_genislik)
            ey = int((slot_data['end_y'] / max(1, self.donanim_yukseklik)) * self.ekran_yukseklik)
                
            sx = max(0, min(sx, self.ekran_genislik)); sy = max(0, min(sy, self.ekran_yukseklik))
            ex = max(0, min(ex, self.ekran_genislik)); ey = max(0, min(ey, self.ekran_yukseklik))
            
            su_an = time.time()
            gecikme = 0.5 if self.son_dokunus_zamani == 0 else round(slot_data['start_time'] - self.son_dokunus_zamani, 2)
            if gecikme > 4.0: gecikme = 4.0
            if gecikme < 0.1: gecikme = 0.1 
            
            mesafe = np.sqrt((ex - sx)**2 + (ey - sy)**2)
            hareket_suresi_ms = max(100, int((su_an - slot_data['start_time']) * 1000))
            
            if mesafe > 60 and hareket_suresi_ms > 80: 
                self.gecici_dokunuslar.append(f"S,{sx},{sy},{ex},{ey},{hareket_suresi_ms},{gecikme}")
                self.after(0, lambda px1=sx, py1=sy, px2=ex, py2=ey: self.log_yaz(f"👆 Kaydırma: ({px1},{py1}) -> ({px2},{py2})"))
            else: 
                self.gecici_dokunuslar.append(f"T,{ex},{ey},{gecikme}")
                self.after(0, lambda px=ex, py=ey: self.log_yaz(f"🎯 Tıklama: X:{px}, Y:{py}"))
                
            # Son dokunuş zamanı güncellendiği için 1.5 saniyelik Akıllı Zeka sayacı sıfırlanır
            self.son_dokunus_zamani = su_an

        while self.kayit_aktif:
            line = self.getevent_proc.stdout.readline()
            if not line: break
            
            if "ABS_MT_SLOT" in line:
                current_slot = int(line.split()[-1], 16)
                if current_slot not in slots: slots[current_slot] = {}
                
            elif "ABS_MT_TRACKING_ID" in line:
                cihaz_mt_destekli = True
                val = line.split()[-1]
                if current_slot not in slots: slots[current_slot] = {}
                
                if val == "ffffffff":
                    if slots[current_slot].get('active'): process_touch(slots[current_slot])
                    slots[current_slot] = {'active': False}
                else:
                    slots[current_slot] = {'active': True, 'start_time': time.time(), 'start_x': None, 'start_y': None, 'end_x': None, 'end_y': None}
                    
            elif "BTN_TOUCH" in line:
                if not cihaz_mt_destekli:
                    val = line.split()[-1]
                    if 0 not in slots: slots[0] = {}
                    if val == "DOWN":
                        if not slots[0].get('active'):
                            slots[0] = {'active': True, 'start_time': time.time(), 'start_x': None, 'start_y': None, 'end_x': None, 'end_y': None}
                    elif val == "UP":
                        if slots[0].get('active'): process_touch(slots[0])
                        slots[0] = {'active': False}
                    
            elif "ABS_MT_POSITION_X" in line:
                val = int(line.split()[-1], 16)
                if current_slot not in slots or not slots[current_slot].get('active'):
                    slots[current_slot] = {'active': True, 'start_time': time.time(), 'start_x': val, 'start_y': None, 'end_x': val, 'end_y': None}
                if slots[current_slot].get('start_x') is None: slots[current_slot]['start_x'] = val
                slots[current_slot]['end_x'] = val
                
            elif "ABS_MT_POSITION_Y" in line:
                val = int(line.split()[-1], 16)
                if current_slot not in slots or not slots[current_slot].get('active'):
                    slots[current_slot] = {'active': True, 'start_time': time.time(), 'start_x': None, 'start_y': val, 'end_x': None, 'end_y': val}
                if slots[current_slot].get('start_y') is None: slots[current_slot]['start_y'] = val
                slots[current_slot]['end_y'] = val

    def arka_planda_case_kaydet(self, case_adi, dokunuslar):
        try:
            c_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            
            # --- DİNAMİK İSİMLENDİRME: Hızlı adımlarda fotoğrafların çarpışmasını tamamen önler ---
            zaman_ms = int(time.time() * 1000)
            cihaz_ref_yolu = f"/sdcard/ref_{zaman_ms}.png"
            ref_isim = f"ref_{self.guncel_test_adi.replace(' ', '_')}_{case_adi.replace(' ', '_')}_{zaman_ms}.png"
            ref_yol = os.path.join(self.referans_klasoru, ref_isim)
            
            subprocess.run([self.adb_yolu, "shell", "screencap", "-p", cihaz_ref_yolu], capture_output=True, creationflags=c_flags)
            subprocess.run([self.adb_yolu, "pull", cihaz_ref_yolu, ref_yol], capture_output=True, creationflags=c_flags)
            subprocess.run([self.adb_yolu, "shell", "rm", cihaz_ref_yolu], capture_output=True, creationflags=c_flags)
                
            aksiyon_str = "|".join(dokunuslar)
            dokunus_sayisi = len(dokunuslar)
            
            conn = sqlite3.connect(self.db_yolu)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO case_bazli_testler VALUES (NULL,?,?,?,?,?,?,?)", 
                         (self.guncel_test_adi, self.guncel_yetkili, self.guncel_uygulama, self.guncel_amac, case_adi, aksiyon_str, ref_isim))
            conn.commit()
            conn.close()
            
            self.after(0, lambda: self.log_yaz(f"✅ Adım '{case_adi}' OTO-KAYDEDİLDİ! ({dokunus_sayisi} Eylem)"))
        except Exception as e:
            self.after(0, lambda: self.log_yaz(f"❌ Kayıt hatası: {e}"))

    def kaydi_bitir_islem(self):
        self.kayit_aktif = False
        if self.klavye_dinleyici:
            self.klavye_dinleyici.stop()
            self.klavye_dinleyici = None
        if self.getevent_proc and self.getevent_proc.poll() is None: 
            self.getevent_proc.terminate()
            
        # Kullanıcı ESC'ye bastığında, eğer sırada bekleyen bir hareket varsa o da boşa gitmesin
        if self.gecici_dokunuslar:
            self.log_yaz(f"\n⏳ Kalan son adımlar paketleniyor...")
            kopya = list(self.gecici_dokunuslar)
            self.gecici_dokunuslar.clear()
            case_adi = f"Adim_{self.adim_sayaci}"
            self.arka_planda_case_kaydet(case_adi, kopya)
            
        try:
            self.btn_baslat.configure(state="normal")
            self.lbl_oto_durum.configure(text="Zeka Bekliyor", fg_color="gray", text_color="white")
            self.btn_bitir.configure(state="disabled")
            self.log_yaz("\n" + "🟩"*25 + "\n🎉 KAYIT TAMAMLANDI VE MOTOR KAPATILDI!\n" + "🟩"*25 + "\n")
        except Exception:
            pass

    def log_yaz(self, mesaj):
        self.log_kutusu.insert("end", mesaj + "\n")
        self.log_kutusu.see("end")

    # ==========================================
    #          2. TEST LİSTELEME VE YÖNETİM
    # ==========================================
    def goster_liste(self):
        self.temizle()
        ctk.CTkLabel(self.main_frame, text="🚀 Kayıtlı Testleri Yönet", font=("Arial", 18, "bold")).pack(pady=10)
        
        ust_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        ust_frame.pack(pady=5, fill="x", padx=10)
        self.arama_entry = ctk.CTkEntry(ust_frame, placeholder_text="Test Adı veya Uygulama Ara...", width=400)
        self.arama_entry.pack(side="left", padx=10)
        self.arama_entry.bind("<KeyRelease>", self.listeyi_guncelle)

        btn_ice_aktar = ctk.CTkButton(ust_frame, text="📥 Test İçe Aktar (.json)", fg_color="#8e44ad", hover_color="#732d91", command=self.testi_ice_aktar)
        btn_ice_aktar.pack(side="right", padx=10)

        self.test_listesi = ctk.CTkScrollableFrame(self.main_frame, width=800, height=400)
        self.test_listesi.pack(pady=10, padx=10, fill="both", expand=True)
        self.listeyi_guncelle()

    def listeyi_guncelle(self, event=None):
        for widget in self.test_listesi.winfo_children(): widget.destroy()
        if not os.path.exists(self.db_yolu): return
        arama_metni = self.arama_entry.get().strip()
        try:
            conn = sqlite3.connect(self.db_yolu)
            cursor = conn.cursor()
            sorgu = "SELECT DISTINCT ana_test_adi, uygulama, yetkili FROM case_bazli_testler WHERE ana_test_adi LIKE ? OR uygulama LIKE ?"
            cursor.execute(sorgu, (f'%{arama_metni}%', f'%{arama_metni}%'))
            kayitlar = cursor.fetchall()
            conn.close()

            if not kayitlar:
                ctk.CTkLabel(self.test_listesi, text="Eşleşen test bulunamadı.").pack(pady=20)
                return

            for test_adi, uygulama, yetkili in kayitlar:
                satir_frame = ctk.CTkFrame(self.test_listesi, fg_color="#2b2b2b", corner_radius=5)
                satir_frame.pack(fill="x", pady=5, padx=5)

                lbl_bilgi = ctk.CTkLabel(satir_frame, text=f"📂 {test_adi}  |  Uyg: {uygulama}  |  Yazan: {yetkili}", anchor="w", font=("Arial", 13, "bold"))
                lbl_bilgi.pack(side="left", padx=15, pady=10, fill="x", expand=True)

                btn_oynat = ctk.CTkButton(satir_frame, text="▶ Oynat", width=70, fg_color="green", hover_color="darkgreen", command=lambda t=test_adi: self.testi_oynat(t))
                btn_oynat.pack(side="right", padx=5, pady=10)
                btn_paylas = ctk.CTkButton(satir_frame, text="📤 Paylaş", width=70, fg_color="#2980b9", hover_color="#1f618d", command=lambda t=test_adi: self.testi_disa_aktar(t))
                btn_paylas.pack(side="right", padx=5, pady=10)
                btn_duzenle = ctk.CTkButton(satir_frame, text="✏️", width=40, fg_color="#F4A460", text_color="black", hover_color="#d68b49", command=lambda t=test_adi, u=uygulama, y=yetkili: self.duzenle_popup_ac(t, u, y))
                btn_duzenle.pack(side="right", padx=5, pady=10)
                btn_sil = ctk.CTkButton(satir_frame, text="🗑️", width=40, fg_color="#c0392b", hover_color="#962d22", command=lambda t=test_adi: self.testi_sil(t))
                btn_sil.pack(side="right", padx=5, pady=10)
        except Exception as e: pass

    def testi_disa_aktar(self, test_adi):
        try:
            conn = sqlite3.connect(self.db_yolu)
            cursor = conn.cursor()
            cursor.execute("SELECT yetkili, uygulama, amac, case_adi, aksiyonlar, beklenen_xml FROM case_bazli_testler WHERE ana_test_adi = ? ORDER BY id ASC", (test_adi,))
            satirlar = cursor.fetchall()
            conn.close()
            if not satirlar: return
            export_data = {
                "ana_test_adi": test_adi, "yetkili": satirlar[0][0], "uygulama": satirlar[0][1], "amac": satirlar[0][2], "caseler": []
            }
            for s in satirlar: export_data["caseler"].append({"case_adi": s[3], "aksiyonlar": s[4], "beklenen_xml": s[5]})

            dosya_ismi = f"{test_adi.replace(' ', '_')}_Testi.json"
            dosya_yolu = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Dosyaları", "*.json")], initialfile=dosya_ismi, title="Testi Bilgisayara Kaydet")
            if dosya_yolu:
                with open(dosya_yolu, "w", encoding="utf-8") as f: json.dump(export_data, f, ensure_ascii=False, indent=4)
                messagebox.showinfo("Başarılı", f"Test dışa aktarıldı!\nDosya: {dosya_yolu}")
        except Exception as e: messagebox.showerror("Hata", f"Dışa aktarma başarısız: {e}")

    def testi_ice_aktar(self):
        dosya_yolu = filedialog.askopenfilename(filetypes=[("JSON Dosyaları", "*.json")], title="İçe Aktarılacak Testi Seçin")
        if not dosya_yolu: return
        try:
            with open(dosya_yolu, "r", encoding="utf-8") as f: data = json.load(f)
            ana_test_adi = data.get("ana_test_adi", "Bilinmeyen Test") + " (İçe Aktarıldı)"
            yetkili = data.get("yetkili", "Bilinmiyor")
            uygulama = data.get("uygulama", "Bilinmiyor")
            amac = data.get("amac", "Paylaşılan test")
            conn = sqlite3.connect(self.db_yolu)
            cursor = conn.cursor()
            for case in data.get("caseler", []):
                cursor.execute("INSERT INTO case_bazli_testler VALUES (NULL,?,?,?,?,?,?,?)", (ana_test_adi, yetkili, uygulama, amac, case["case_adi"], case["aksiyonlar"], case["beklenen_xml"]))
            conn.commit()
            conn.close()
            self.listeyi_guncelle()
            messagebox.showinfo("Başarılı", f"'{ana_test_adi}' başarıyla sisteme eklendi!")
        except Exception as e: messagebox.showerror("Hata", f"Hata: {e}")

    def testi_sil(self, test_adi):
        try:
            conn = sqlite3.connect(self.db_yolu)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM case_bazli_testler WHERE ana_test_adi = ?", (test_adi,))
            conn.commit()
            conn.close()
            self.listeyi_guncelle()
        except Exception as e: pass

    def duzenle_popup_ac(self, eski_ad, eski_uyg, eski_yetkili):
        popup = ctk.CTkToplevel(self)
        popup.title("Testi Düzenle")
        popup.geometry("400x350")
        popup.attributes("-topmost", True)
        ctk.CTkLabel(popup, text=f"'{eski_ad}' Düzenleniyor", font=("Arial", 16, "bold")).pack(pady=15)
        yeni_ad_entry = ctk.CTkEntry(popup, width=250)
        yeni_ad_entry.insert(0, eski_ad)
        yeni_ad_entry.pack(pady=10)
        yeni_uyg_entry = ctk.CTkEntry(popup, width=250)
        yeni_uyg_entry.insert(0, eski_uyg)
        yeni_uyg_entry.pack(pady=10)
        yeni_yetkili_entry = ctk.CTkEntry(popup, width=250)
        yeni_yetkili_entry.insert(0, eski_yetkili)
        yeni_yetkili_entry.pack(pady=10)

        def kaydet():
            y_ad = yeni_ad_entry.get()
            y_uyg = yeni_uyg_entry.get()
            y_yetkili = yeni_yetkili_entry.get()
            if y_ad:
                conn = sqlite3.connect(self.db_yolu)
                cursor = conn.cursor()
                cursor.execute("UPDATE case_bazli_testler SET ana_test_adi = ?, uygulama = ?, yetkili = ? WHERE ana_test_adi = ?", (y_ad, y_uyg, y_yetkili, eski_ad))
                cursor.execute("UPDATE test_sonuclari SET ana_test_adi = ? WHERE ana_test_adi = ?", (y_ad, eski_ad))
                conn.commit()
                conn.close()
                popup.destroy()
                self.listeyi_guncelle()

        ctk.CTkButton(popup, text="💾 Değişiklikleri Kaydet", fg_color="green", hover_color="darkgreen", command=kaydet).pack(pady=20)

    # ==========================================
    #   3. OYNATMA VE CANLI GÖRSEL DASHBOARD
    # ==========================================
    def testi_oynat(self, test_adi):
        dialog = ctk.CTkInputDialog(text=f"'{test_adi}' testi art arda kaç kez çalıştırılsın?\n(Sadece 1 kez için 1 yazın)", title="Döngü Sayısı")
        cevap = dialog.get_input()
        if cevap is None: return
        try:
            tekrar_sayisi = int(cevap)
            if tekrar_sayisi <= 0: tekrar_sayisi = 1
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli bir tam sayı girin!")
            return

        self.oynatma_penceresi = ctk.CTkToplevel(self)
        self.oynatma_penceresi.title(f"Test Yürütülüyor: {test_adi} ({tekrar_sayisi} Tekrar)")
        self.oynatma_penceresi.geometry("1100x650")
        self.oynatma_penceresi.attributes("-topmost", True)
        
        self.log_frame = ctk.CTkFrame(self.oynatma_penceresi, width=350)
        self.log_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        lbl_baslik = ctk.CTkLabel(self.log_frame, text=f"🚀 Test Logları", font=("Arial", 16, "bold"))
        lbl_baslik.pack(pady=10)
        
        self.canli_log = ctk.CTkTextbox(self.log_frame, width=350, font=("Consolas", 12))
        self.canli_log.pack(fill="both", expand=True, padx=5, pady=5)
        self.canli_log.insert("end", f"[SİSTEM] ADB bağlantısı kuruluyor...\n\n")

        self.img_frame = ctk.CTkFrame(self.oynatma_penceresi)
        self.img_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        title_frame = ctk.CTkFrame(self.img_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(title_frame, text="Beklenen (Referans)", font=("Arial", 14, "bold")).pack(side="left", expand=True)
        ctk.CTkLabel(title_frame, text="Anlık Cihaz (Hatalar İşaretli)", font=("Arial", 14, "bold")).pack(side="right", expand=True)
        
        images_container = ctk.CTkFrame(self.img_frame, fg_color="transparent")
        images_container.pack(fill="both", expand=True, pady=5)
        
        self.lbl_img_ref = ctk.CTkLabel(images_container, text="⏳ Test Bekleniyor...", width=300, height=480, fg_color="#2b2b2b")
        self.lbl_img_ref.pack(side="left", expand=True, padx=10)
        
        self.lbl_img_check = ctk.CTkLabel(images_container, text="⏳ Test Bekleniyor...", width=300, height=480, fg_color="#2b2b2b")
        self.lbl_img_check.pack(side="right", expand=True, padx=10)
        
        self.lbl_benzerlik = ctk.CTkLabel(self.img_frame, text="Benzerlik: Analiz Bekleniyor...", font=("Arial", 18, "bold"))
        self.lbl_benzerlik.pack(pady=10)

        threading.Thread(target=self.arka_planda_oynat, args=(test_adi, tekrar_sayisi), daemon=True).start()

    def ui_gorsel_guncelle(self, ref_yol, check_yol, skor_yuzde):
        try:
            img_ref = Image.open(ref_yol)
            img_check = Image.open(check_yol)
            
            oran = 480 / img_ref.height
            yeni_boyut = (int(img_ref.width * oran), 480)
            
            ctk_ref = ctk.CTkImage(light_image=img_ref, size=yeni_boyut)
            ctk_check = ctk.CTkImage(light_image=img_check, size=yeni_boyut)
            
            self.lbl_img_ref.configure(image=ctk_ref, text="")
            self.lbl_img_check.configure(image=ctk_check, text="")
            
            renk = "lightgreen" if skor_yuzde >= 85 else "#ff4d4d"
            self.lbl_benzerlik.configure(text=f"Analiz Edilen Benzerlik: %{skor_yuzde}", text_color=renk)
        except Exception: pass

    def goruntu_kiyasla_ve_isaretle(self, ref_yol, check_yol):
        try:
            img_ref_color = cv2.imdecode(np.fromfile(ref_yol, dtype=np.uint8), cv2.IMREAD_COLOR)
            img_check_color = cv2.imdecode(np.fromfile(check_yol, dtype=np.uint8), cv2.IMREAD_COLOR)
            
            if img_ref_color is None or img_check_color is None:
                return 0.0, check_yol
                
            img1 = cv2.cvtColor(img_ref_color, cv2.COLOR_BGR2GRAY)
            img2 = cv2.cvtColor(img_check_color, cv2.COLOR_BGR2GRAY)
            
            if img1.shape != img2.shape:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
                img_check_color = cv2.resize(img_check_color, (img1.shape[1], img1.shape[0]))
                
            fark = cv2.absdiff(img1, img2)
            _, thresh = cv2.threshold(fark, 30, 255, cv2.THRESH_BINARY)
            
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in contours:
                if cv2.contourArea(c) > 100: 
                    x, y, w, h = cv2.boundingRect(c)
                    cv2.rectangle(img_check_color, (x, y), (x+w, y+h), (0, 0, 255), 3) 
                    
            farkli_piksel_sayisi = cv2.countNonZero(thresh)
            toplam_piksel = img1.shape[0] * img1.shape[1]
            benzerlik = 1.0 - (farkli_piksel_sayisi / toplam_piksel)
            
            fark_yol = os.path.join(self.hata_klasoru, "temp_diff.png")
            is_success, im_buf_arr = cv2.imencode(".png", img_check_color)
            if is_success: im_buf_arr.tofile(fark_yol)
            else: cv2.imwrite(fark_yol, img_check_color)
            
            return benzerlik, fark_yol
        except Exception:
            return 0.0, check_yol

    def arka_planda_oynat(self, test_adi, tekrar_sayisi):
        c_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        def ekrana_yaz(mesaj):
            self.canli_log.insert("end", mesaj + "\n")
            self.canli_log.see("end")

        try:
            conn = sqlite3.connect(self.db_yolu)
            cursor = conn.cursor()
            cursor.execute("SELECT case_adi, aksiyonlar, beklenen_xml FROM case_bazli_testler WHERE ana_test_adi = ? ORDER BY id ASC", (test_adi,))
            cases = cursor.fetchall()
            conn.close()

            if not cases:
                ekrana_yaz("❌ Bu teste ait hiçbir case (adım) bulunamadı!")
                return

            for dongu in range(1, tekrar_sayisi + 1):
                ekrana_yaz(f"\n" + "="*35)
                ekrana_yaz(f"🔄 DÖNGÜ BAŞLIYOR: {dongu}/{tekrar_sayisi}")
                ekrana_yaz("="*35 + "\n")

                zaman_damgasi = int(time.time())
                log_dosya_adi = f"log_{test_adi.replace(' ', '_')}_D{dongu}_{zaman_damgasi}.txt"
                log_yolu = os.path.join(self.log_klasoru, log_dosya_adi)
                
                subprocess.run([self.adb_yolu, "logcat", "-c"], creationflags=c_flags)
                log_dosyasi = open(log_yolu, "w", encoding="utf-8")
                log_proc = subprocess.Popen([self.adb_yolu, "logcat", "-v", "threadtime"], stdout=log_dosyasi, creationflags=c_flags)

                toplam_adim = len(cases)
                basarili_adim = 0
                adim_raporlari = []
                dongu_iptal = False

                for c_adi, aksiyonlar, ref_veri in cases:
                    dokunuslar = [n for n in aksiyonlar.split("|") if n]
                    ekrana_yaz(f"⏳ '{c_adi}' uygulanıyor...")
                    
                    for nokta in dokunuslar:
                        veriler = nokta.split(",")
                        islem_turu = veriler[0]

                        if islem_turu == "T": 
                            x, y, bekleme = veriler[1], veriler[2], float(veriler[3])
                            time.sleep(bekleme)
                            subprocess.run([self.adb_yolu, "shell", "input", "tap", x, y], creationflags=c_flags)
                            
                        elif islem_turu == "S": 
                            x1, y1, x2, y2, dur, bekleme = veriler[1], veriler[2], veriler[3], veriler[4], veriler[5], float(veriler[6])
                            time.sleep(bekleme)
                            subprocess.run([self.adb_yolu, "shell", "input", "swipe", x1, y1, x2, y2, dur], creationflags=c_flags)
                            
                        else: 
                            if len(veriler) >= 2 and veriler[0].isdigit():
                                x, y = veriler[0], veriler[1]
                                bekleme = float(veriler[2]) if len(veriler) > 2 else 0.2
                                time.sleep(bekleme)
                                subprocess.run([self.adb_yolu, "shell", "input", "tap", x, y], creationflags=c_flags)
                    
                    time.sleep(1.5) 

                    ekrana_yaz(f"🔍 '{c_adi}' AI ile taranıyor...")
                    
                    # --- ÇARPIŞMAYI ÖNLEYEN DEVRİM OYNATIRKEN DE AKTİF ---
                    zaman_ms_oynat = int(time.time() * 1000)
                    cihaz_check_yolu = f"/sdcard/check_{zaman_ms_oynat}.png"
                    test_foto_isim = f"temp_check_{zaman_ms_oynat}.png"
                    test_foto_yol = os.path.join(self.hata_klasoru, test_foto_isim)
                    
                    subprocess.run([self.adb_yolu, "shell", "screencap", "-p", cihaz_check_yolu], capture_output=True, creationflags=c_flags)
                    subprocess.run([self.adb_yolu, "pull", cihaz_check_yolu, test_foto_yol], capture_output=True, creationflags=c_flags)
                    subprocess.run([self.adb_yolu, "shell", "rm", cihaz_check_yolu], capture_output=True, creationflags=c_flags)
                    
                    if ref_veri.endswith(".png"):
                        referans_tam_yol = os.path.join(self.referans_klasoru, ref_veri)
                        if os.path.exists(referans_tam_yol) and os.path.exists(test_foto_yol):
                            
                            skor, isaretli_foto_yol = self.goruntu_kiyasla_ve_isaretle(referans_tam_yol, test_foto_yol)
                            skor_yuzde = int(skor * 100)
                            
                            self.after(0, lambda r=referans_tam_yol, c=isaretli_foto_yol, s=skor_yuzde: self.ui_gorsel_guncelle(r, c, s))
                            
                            # --- HATA BULUNDUĞUNDA SİSTEMİ DURDURAN YENİ KURAL ---
                            if skor < 0.85:
                                ekrana_yaz(f"❌ BAŞARISIZ! (Benzerlik: %{skor_yuzde})\n" + "-"*35)
                                foto_isim = f"hata_{test_adi.replace(' ', '_')}_D{dongu}_{c_adi.replace(' ', '_')}_{int(time.time())}.png"
                                foto_yol = os.path.join(self.hata_klasoru, foto_isim)
                                os.rename(isaretli_foto_yol, foto_yol) 
                                adim_raporlari.append(f"❌ {c_adi} - BAŞARISIZ (Benzerlik: %{skor_yuzde}) | IMG:{foto_yol}")
                                if os.path.exists(test_foto_yol): os.remove(test_foto_yol)
                                
                                ekrana_yaz("🛑 HATA TESPİT EDİLDİ! Oynatma durduruluyor...")
                                dongu_iptal = True
                                break # Oynatmayı anında keser!
                            else:
                                ekrana_yaz(f"✅ BAŞARILI! (Benzerlik: %{skor_yuzde})\n" + "-"*35)
                                basarili_adim += 1
                                adim_raporlari.append(f"✅ {c_adi} - BAŞARILI (Benzerlik: %{skor_yuzde})")
                                if os.path.exists(isaretli_foto_yol): os.remove(isaretli_foto_yol) 
                                if os.path.exists(test_foto_yol): os.remove(test_foto_yol) 
                        else:
                            ekrana_yaz(f"⚠️ {c_adi} OKUNAMADI (Referans Yok).\n" + "-"*35)
                            adim_raporlari.append(f"⚠️ {c_adi} - OKUNAMADI")
                            if os.path.exists(test_foto_yol): os.remove(test_foto_yol)
                    else:
                        ekrana_yaz(f"⚠️ ESKİ KAYIT! (Lütfen baştan kaydedin).\n" + "-"*35)
                        adim_raporlari.append(f"⚠️ {c_adi} - ESKİ KAYIT TÜRÜ")
                        if os.path.exists(test_foto_yol): os.remove(test_foto_yol)
                        
                log_proc.terminate()
                log_dosyasi.close()
                adim_raporlari.append(f"📄 LOG DOSYASI | LOG:{log_yolu}")

                genel_durum = "BAŞARILI" if basarili_adim == toplam_adim else "BAŞARISIZ"
                tarih_saat = datetime.now().strftime("%d-%m-%Y %H:%M")
                detaylar_str = "\n".join(adim_raporlari)
                test_dongu_adi = f"{test_adi} (Döngü {dongu})" if tekrar_sayisi > 1 else test_adi

                kayit_conn = sqlite3.connect(self.db_yolu)
                kayit_cursor = kayit_conn.cursor()
                try:
                    kayit_cursor.execute("INSERT INTO test_sonuclari (ana_test_adi, tarih, toplam_adim, basarili_adim, genel_durum, detaylar) VALUES (?,?,?,?,?,?)", 
                                 (test_dongu_adi, tarih_saat, toplam_adim, basarili_adim, genel_durum, detaylar_str))
                except Exception:
                    kayit_cursor.execute("INSERT INTO test_sonuclari VALUES (NULL,?,?,?,?,?)", 
                                 (test_dongu_adi, tarih_saat, toplam_adim, basarili_adim, genel_durum))
                kayit_conn.commit()
                kayit_conn.close()
                ekrana_yaz(f"💾 Döngü {dongu} raporlandı!\n")
                
                # Eğer hata bulunduysa sonraki döngüleri de çalıştırma
                if dongu_iptal:
                    ekrana_yaz("\n⚠️ Kritik hata sebebiyle test zinciri iptal edildi.")
                    break
                    
                if dongu < tekrar_sayisi: time.sleep(1.5)

            if not dongu_iptal:
                ekrana_yaz(f"\n🎉 TÜM {tekrar_sayisi} DÖNGÜ BİTTİ!")

        except Exception as e:
            ekrana_yaz(f"\n❌ Kritik Hata: {str(e)}")

    # ==========================================
    #          5. TEST RAPORLARI VE DETAY
    # ==========================================
    def goster_raporlar(self):
        self.temizle()
        ctk.CTkLabel(self.main_frame, text="📊 Geçmiş Test Sonuç Raporları", font=("Arial", 18, "bold")).pack(pady=10)
        ust_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        ust_frame.pack(pady=5, fill="x", padx=10)
        self.arama_rapor_entry = ctk.CTkEntry(ust_frame, placeholder_text="Raporlarda Test Adı Ara...", width=400)
        self.arama_rapor_entry.pack(side="left", padx=10)
        self.arama_rapor_entry.bind("<KeyRelease>", self.rapor_listeyi_guncelle)

        self.rapor_listesi = ctk.CTkScrollableFrame(self.main_frame, width=800, height=450)
        self.rapor_listesi.pack(pady=10, padx=10, fill="both", expand=True)
        self.rapor_listeyi_guncelle()

    def rapor_listeyi_guncelle(self, event=None):
        for widget in self.rapor_listesi.winfo_children(): widget.destroy()
        try:
            conn = sqlite3.connect(self.db_yolu)
            cursor = conn.cursor()
            arama_metni = self.arama_rapor_entry.get().strip() if hasattr(self, 'arama_rapor_entry') else ""
            sorgu = "SELECT id, ana_test_adi, tarih, toplam_adim, basarili_adim, genel_durum, detaylar FROM test_sonuclari WHERE ana_test_adi LIKE ? ORDER BY id DESC"
            cursor.execute(sorgu, (f'%{arama_metni}%',))
            raporlar = cursor.fetchall()
            conn.close()

            if not raporlar:
                ctk.CTkLabel(self.rapor_listesi, text="Arama sonucunda rapor bulunamadı.", text_color="yellow").pack(pady=20)
                return

            for r_id, test_adi, tarih, toplam, basarili, durum, detaylar in raporlar:
                arka_plan_rengi = "darkgreen" if durum == "BAŞARILI" else "#962d22"
                satir = ctk.CTkFrame(self.rapor_listesi, fg_color=arka_plan_rengi, corner_radius=5)
                satir.pack(fill="x", pady=5, padx=5)

                bilgi_metni = f"🕒 {tarih}   |   📂 {test_adi}   |   Başarı: {basarili}/{toplam}"
                ctk.CTkLabel(satir, text=bilgi_metni, font=("Arial", 13, "bold")).pack(side="left", padx=15, pady=10)
                btn_sil = ctk.CTkButton(satir, text="🗑️ Sil", width=60, fg_color="#c0392b", hover_color="#962d22", command=lambda idx=r_id: self.raporu_sil(idx))
                btn_sil.pack(side="right", padx=5, pady=10)
                btn_paylas = ctk.CTkButton(satir, text="📤 Paylaş (ZIP)", width=100, fg_color="#2980b9", hover_color="#1f618d", command=lambda t=test_adi, dt=tarih, tp=toplam, b=basarili, dr=durum, d=detaylar: self.raporu_zip_paylas(t, dt, tp, b, dr, d))
                btn_paylas.pack(side="right", padx=5, pady=10)
                btn_detay = ctk.CTkButton(satir, text="🔍 Detaylar", width=80, fg_color="#1f538d", hover_color="#14375e", command=lambda t=test_adi, dt=tarih, d=detaylar: self.detay_popup_ac(t, dt, d))
                btn_detay.pack(side="right", padx=5, pady=10)
        except Exception as e: pass

    def raporu_sil(self, rapor_id):
        cevap = messagebox.askyesno("Onay", "Bu test raporunu kalıcı olarak silmek istediğinize emin misiniz?\n(Fotoğraf ve log dosyaları da diskten silinecektir.)")
        if not cevap: return
        try:
            conn = sqlite3.connect(self.db_yolu)
            cursor = conn.cursor()
            cursor.execute("SELECT detaylar FROM test_sonuclari WHERE id = ?", (rapor_id,))
            kayit = cursor.fetchone()
            if kayit and kayit[0]:
                for satir in kayit[0].split("\n"):
                    if "| IMG:" in satir:
                        yol = satir.split("| IMG:")[1].strip()
                        if os.path.exists(yol): os.remove(yol)
                    elif "| LOG:" in satir:
                        yol = satir.split("| LOG:")[1].strip()
                        if os.path.exists(yol): os.remove(yol)
            cursor.execute("DELETE FROM test_sonuclari WHERE id = ?", (rapor_id,))
            conn.commit()
            conn.close()
            self.rapor_listeyi_guncelle()
        except Exception as e: messagebox.showerror("Hata", f"Rapor silinirken hata oluştu: {e}")

    def raporu_zip_paylas(self, test_adi, tarih, toplam, basarili, durum, detaylar):
        dosya_tarih = tarih.replace(":", "-").replace(" ", "_")
        zip_ismi = f"Rapor_{test_adi.replace(' ', '_')}_{dosya_tarih}.zip"
        zip_yolu = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP Dosyaları", "*.zip")], initialfile=zip_ismi, title="Raporu ZIP Olarak Kaydet")
        if not zip_yolu: return
        try:
            rapor_icerik = "="*55 + "\n           OTOMASYON TEST SONUÇ RAPORU\n" + "="*55 + "\n\n"
            rapor_icerik += f"📌 Test Adı       : {test_adi}\n🕒 Çalışma Tarihi : {tarih}\n📊 Başarı Oranı   : {basarili} / {toplam} Adım Başarılı\n🎯 Genel Durum    : {durum}\n\n--- ADIM BAZLI DETAYLAR ---\n"
            eklenecek_dosyalar = []
            if detaylar:
                for satir in detaylar.split("\n"):
                    if "| IMG:" in satir:
                        metin, yol = satir.split("| IMG:")
                        rapor_icerik += metin.strip() + f" (Hata Görseli Zip İçinde: {os.path.basename(yol.strip())})\n"
                        if os.path.exists(yol.strip()): eklenecek_dosyalar.append(yol.strip())
                    elif "| LOG:" in satir:
                        metin, yol = satir.split("| LOG:")
                        rapor_icerik += metin.strip() + f" (Log Dosyası Zip İçinde: {os.path.basename(yol.strip())})\n"
                        if os.path.exists(yol.strip()): eklenecek_dosyalar.append(yol.strip())
                    else: rapor_icerik += satir + "\n"
            else: rapor_icerik += "Detay bulunamadı.\n"
            rapor_icerik += "\n" + "="*55 + "\n"
            with zipfile.ZipFile(zip_yolu, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr(f"Test_Sonuc_Raporu_{dosya_tarih}.txt", rapor_icerik)
                for dosya in set(eklenecek_dosyalar): zipf.write(dosya, arcname=os.path.basename(dosya))
            messagebox.showinfo("Başarılı", f"Rapor, Log dosyası ve Hata görüntüleri başarıyla ZIP olarak paketlendi!\n\nDosya: {zip_yolu}")
        except Exception as e: messagebox.showerror("Hata", f"Rapor paketlenirken hata oluştu: {e}")

    def detay_popup_ac(self, test_adi, tarih, detaylar):
        popup = ctk.CTkToplevel(self)
        popup.title("Test Adım Detayları")
        popup.geometry("550x650") 
        popup.attributes("-topmost", True)
        ctk.CTkLabel(popup, text=f"📂 {test_adi}\n🕒 {tarih}", font=("Arial", 16, "bold")).pack(pady=10)
        scroll_alan = ctk.CTkScrollableFrame(popup, width=500, height=550)
        scroll_alan.pack(padx=10, pady=10, fill="both", expand=True)
        if detaylar:
            for satir in detaylar.split("\n"):
                if "| IMG:" in satir:
                    metin_kismi, foto_yolu = satir.split("| IMG:")
                    ctk.CTkLabel(scroll_alan, text=metin_kismi.strip(), font=("Arial", 14, "bold"), text_color="#ff4d4d").pack(pady=(15, 5), anchor="w", padx=10)
                    if os.path.exists(foto_yolu.strip()):
                        try:
                            orijinal_resim = Image.open(foto_yolu.strip())
                            oran = 300 / orijinal_resim.width
                            yeni_boyut = (300, int(orijinal_resim.height * oran))
                            ctk_img = ctk.CTkImage(light_image=orijinal_resim, dark_image=orijinal_resim, size=yeni_boyut)
                            lbl_resim = ctk.CTkLabel(scroll_alan, image=ctk_img, text="")
                            lbl_resim.pack(pady=5, anchor="w", padx=30)
                        except Exception: pass
                    else: ctk.CTkLabel(scroll_alan, text="⚠️ Ekran görüntüsü bulunamadı.", text_color="yellow").pack(anchor="w", padx=30)
                elif "| LOG:" in satir:
                    metin_kismi, log_yolu = satir.split("| LOG:")
                    if os.path.exists(log_yolu.strip()): ctk.CTkButton(scroll_alan, text="📄 Tüm Cihaz Logunu (Logcat) Göster", fg_color="#8e44ad", hover_color="#732d91", command=lambda p=log_yolu.strip(): os.startfile(p)).pack(pady=(20, 10), padx=30, fill="x")
                    else: ctk.CTkLabel(scroll_alan, text="⚠️ Log dosyası silinmiş.", text_color="yellow").pack(anchor="w", padx=30)
                else:
                    renk = "lightgreen" if "✅" in satir else ("white" if "⚠️" in satir else "white")
                    ctk.CTkLabel(scroll_alan, text=satir.strip(), font=("Arial", 14, "bold"), text_color=renk).pack(pady=(15, 5), anchor="w", padx=10)
        else: ctk.CTkLabel(scroll_alan, text="⚠️ Adım detayı bulunmuyor.").pack(pady=20)

if __name__ == "__main__":
    app = TestOtomasyonApp()
    app.mainloop()