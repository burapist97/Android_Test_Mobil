<div align="center">
  <img src="app_logo.png" alt="Token Mobile Automation Tool Logo" width="250">
</div>

> Token Finansal Teknolojiler firması adına geliştirilmiş, Android cihazlar üzerinde senaryo bazlı otomatik arayüz (UI) testleri gerçekleştiren merkezi masaüstü otomasyon uygulaması. Cihaz üzerindeki işlemleri kaydederek öğrenir, adımları birebir tekrarlar ve sonuçları XML bazlı karşılaştırarak hataları otonom olarak raporlar.

## ✨ Temel Özellikler

* **Otonom Senaryo Kaydı:** Cihaz üzerindeki kullanıcı etkileşimlerini (dokunuşları) ve ekran dizilimlerini anlık olarak kaydeder, kod yazmaya gerek kalmadan test caseleri oluşturur.
* **Gelişmiş Doğrulama:** Yürütülen testin başarılı olup olmadığını anlamak için güncel ekranın XML dökümünü, referans alınan XML ile karşılaştırır.
* **Detaylı Hata Raporlama (Log & Görüntü):** Bir adımla beklenen sonuç uyuşmazsa, anında ekran görüntüsü (screenshot) alır ve o ana ait detaylı cihaz loglarını (logcat) yakalar. Tüm bu raporlar tek tıkla `.zip` olarak dışa aktarılabilir.
* **Yapay Zeka Destekli Altyapı:** Tüm süreç ve uygulama geliştirme yaşam döngüsü yapay zeka desteği ile tasarlanıp kurgulanmıştır.

## 🛠️ Sistem Gereksinimleri

Uygulamanın sorunsuz çalışabilmesi için aşağıdaki yapılandırmaların hazır olması gerekmektedir:

* **İşletim Sistemi:** Windows 10 veya Windows 11
* **Cihaz Bağlantısı:** USB kablosu ile bilgisayara bağlanmış fiziksel bir Android cihaz veya aktif bir Emulator.
* **Geliştirici Seçenekleri:** Test edilecek Android cihazda **"USB Hata Ayıklama" (USB Debugging)** özelliğinin açık olması zorunludur.

## 🚀 Kurulum

Sistemi kullanmaya başlamak için herhangi bir harici kütüphane veya sürücü kurmanıza gerek yoktur, her şey kurulum paketi içinde dahili olarak gelir.

1. **Kurulum Dosyasını İndirin:** Repository'de yer alan veya paylaşılan güncel `Otomasyon_Kurulum.exe` dosyasını bilgisayarınıza indirin.
2. **Uygulamayı Kurun:** `.exe` dosyasını çalıştırarak sihirbaz adımlarını takip edin. Gerekli tüm sürücüler, ADB araçları ve veritabanı dosyaları otomatik olarak yapılandırılacaktır.
3. **Cihazı Bağlayın:** Android cihazınızı bilgisayara bağlayın ve ekrana gelen "USB Hata Ayıklamasına İzin Ver" uyarısını onaylayın.
4. **Çalıştırın:** Masaüstündeki uygulama simgesine tıklayarak test otomasyon merkezini başlatın.

## 📖 Kullanım ve Akış

1. **Test Kaydı:** Sol menüden `Yeni Kayıt Oluştur` sekmesine gidin. Senaryo adını girip "Kaydı Başlat"a bastığınızda, cihaz üzerinde yaptığınız her adım dinlenmeye başlanır. Her işlem bitiminde Enter (veya ilgili buton) ile adımı isimlendirerek kaydedin.
2. **Test Yürütme:** `Testleri Yönet & Çalıştır` panelinden kaydettiğiniz bir testi seçin ve kaç döngü çalışacağını belirleyerek yürütmeyi başlatın.
3. **Takip ve İnceleme:** Uygulama adımları sırayla işler. Test bitiminde `Test Raporları` menüsünden hata ekran görüntülerini ve log dosyalarını inceleyebilir, ekiple paylaşmak üzere arşivleyebilirsiniz.

## ⚠️ Önemli Uyarılar ve Limitasyonlar

* **Canlı Takip:** Bu uygulama otonom olmasına rağmen belirli ekran gecikmelerinde veya beklenmedik sistem popup'larında hata yapabilmektedir. Testi başlatan kişinin ekran akışını gözlemlemesi tavsiye edilir.
* **Senaryo Güncellemeleri:** Test edilen uygulamaya yeni bir güncelleme geldiğinde (butonların yeri değiştiğinde veya yeni bir ekran eklendiğinde), eski test senaryoları geçersiz olabilir. Bu durumda hata alınan senaryonun akışa yeniden öğretilmesi (kaydedilmesi) beklenmektedir.

---

## 👨‍💻 Geliştirici ve İletişim

**Mahmut Burak Ceylan**
* Uygulamanın geliştirilmesi, teknik sorunlar ve hata bildirimleri (bug raporları) için doğrudan benimle iletişime geçebilirsiniz.

* 🔗 **Proje Repository & Güncel Sürümler (Bugfix):** [more_automation GitHub Sayfası](https://github.com/burapist97/more_automation)

> *Fikir ve kullanım hakları saklıdır.*
