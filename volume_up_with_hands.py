import cv2                       # Görüntü işleme için OpenCV
import mediapipe as mp           # Elleri tanımak için Mediapipe
from math import hypot           # İki kordinat arası mesafeyi hesaplamak için hypot fonksiyonu kullanacağız
from ctypes import cast, POINTER # Hoparlör erişimi için ctypes ve POINTER
from comtypes import CLSCTX_ALL  # Hoparlör erişimi için comtypes ve CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # Hoparlör kontrolü için pycaw
import numpy as np               # Matematik işlemleri ve diziler için NumPy
import time                      # Zaman işlemleri için time modülü

# Kamera kontrolü yapılır
cap = cv2.VideoCapture(0)

# Mediapipe ile elleri tanıma
mpHands = mp.solutions.hands # Mediapipe kütüphanesinin solutions modülünden hands alt modülünü mpHands değişkenine atar.
hands = mpHands.Hands()  #mpHands değişkeninde tanımlanan Hands() sınıfını kullanarak bir hands nesnesi oluşturur.
mpDraw = mp.solutions.drawing_utils #Mediapipe kütüphanesinin solutions.drawing_utils modülünü mpDraw değişkenine atar. Bu modül, Mediapipe'in çizim işlevselliğini sağlar ve tanınan ellerin üzerine çizim yapmak için kullanılır.

# Hoparlör erişimi için pycaw kütüphanesi kullanılır
devices = AudioUtilities.GetSpeakers() #Bilgisayarın mevcut hoparlörlerine erişir. Bu yöntem, mevcut hoparlör cihazlarının bir listesini döndürür.
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None) #1-parametresi, hoparlörlerin arayüzünü tanımlayan bir GUID'dir. 2-Arayüzün etkinleştirilmesi için gereken bağlamı belirtir. None parametresi, özel bir etkinleştirme flag'ı olmadığını belirtir.
volume = cast(interface, POINTER(IAudioEndpointVolume)) #Hoparlörlerin ses seviyesini kontrol etmek için gerekli olan arayüzü temsil eden bir nesne oluşturur.
volbar = 400 #Ses seviyesi bar'ın değeri
volper = 0   #Ses seviyesi % değeri

volMin, volMax = volume.GetVolumeRange()[:2] #Ses değerleri 2 elemanlı bir dizideki elemanlara aktarılır

while True:
    time.sleep(1) #Programı bir saniye beklet

    # Kamera çalışıyorsa görüntü alınır
    success, img = cap.read()
    if not success:  #Hata alınırsa hata mesajını konsola yazar
        print("Görüntü yakalanamadı!")
        continue
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # RGB'ye dönüştürülür

    # Eller hakkında bilgi toplanır
    results = hands.process(imgRGB)

    lmList = []  # Boş liste oluşturulur
    if results.multi_hand_landmarks:    #results nesnesinde birden fazla el belirlendiyse içerisindeki kodu çalıştırır
        for handlandmark in results.multi_hand_landmarks: #Nesnedeki tüm eller için bunu gerçekleştirir
            for id, lm in enumerate(handlandmark.landmark): #Bu iç içe döngü, her elin landmark'larını (lm) ve bu landmark'ların indislerini (id) alır. enumerate() fonksiyonu, bir listenin elemanlarını numaralandırır.
                h, w, _ = img.shape  #Görüntünün yüksekliğini (h) ve genişliğini (w) alır.'_' kısmı renk kanllarının sayısını tespit eder(Burada kullanmıyoruz)
                cx, cy = int(lm.x * w), int(lm.y * h)  # her bir landmark'ın görüntü üzerindeki (x, y) koordinatlarını (cx, cy) hesaplar. Landmark'ların x ve y koordinatları, orijinal görüntünün genişliği ve yüksekliği ile çarpılarak piksel cinsinden ifade edilir.
                lmList.append([id, cx, cy]) # her bir landmark'ın id'si ve piksel cinsinden koordinatlarından oluşan bir liste oluşturur ve bu listeyi lmList listesine ekler.

    if lmList != []: #Liste boş değilse yap
        x1, y1 = lmList[4][1], lmList[4][2]  # Başparmak
        x2, y2 = lmList[8][1], lmList[8][2]  # İşaret parmağı

        # Başparmak ve işaret parmağı uçlarına daire çizilir
        cv2.circle(img, (x1, y1), 13, (255, 0, 0), cv2.FILLED) #çizilecek görüntü,daire merkezi ,daire yarıçapı ,rengi ,daire kenar kalınlığı
        cv2.circle(img, (x2, y2), 13, (255, 0, 0), cv2.FILLED)
        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 3)  # İki parmak ucu arasında bir çizgi çizilir

        length = hypot(x2 - x1, y2 - y1)  #İki parmak arası uzaklık ölçülür

        #Değerler aralıklarını uyarlama yaparak dönüştürür. length değerini;
        vol = np.interp(length, [30, 350], [volMin, volMax]) # 30, 50 => volMin, volMax yapar
        volbar = np.interp(length, [30, 350], [400, 150])
        volper = np.interp(length, [30, 350], [0, 100])

        print(vol, int(length)) # Bu satır, vol ve length değerlerini ekrana yazdırır. vol, parmaklar arasındaki mesafeye göre hesaplanan ses seviyesini temsil eder. length ise başparmak ve işaret parmağı arasındaki mesafeyi ifade eder
        volume.SetMasterVolumeLevel(vol, None) # Ses seviyesini ayarlar. vol değeri, parmaklar arasındaki mesafeye göre hesaplanan ses seviyesini temsil eder. None ise, ses seviyesini değiştiren bir uygulamanın kimliği anlamına gelir

        # Parmak uzunluğuna göre ses seviyesini gösteren bir level bar oluşturulur
        cv2.rectangle(img, (50, 150), (85, 400), (0, 0, 255), 4)   #çizilecek görüntü, sol üst köşe ,sağ alt köşe ,blue:green:red değeri, dikdörtgen kalınlığı
        cv2.rectangle(img, (50, int(volbar)), (85, 400), (0, 0, 255), cv2.FILLED)  #çizilecek görüntü,sol üst köşe, sağ alt köşe ,blue:green:red değeri, dikdörtgenin içini doldur komutu
        cv2.putText(img, f"{int(volper)}%", (10, 40), cv2.FONT_ITALIC, 1, (0, 255, 98), 3)  #yazılacak görüntü, metin, sol üst köşe, yazı tipi, metin boyutu, metin rengi, metin kalınlığı

    cv2.imshow('Image', img)  # Video gösterilir
    if cv2.waitKey(1) & 0xff == ord(' '):  # Boşluk tuşu ile döngü sonlandırılır
        break

cap.release()  # Kamera serbest bırakılır
cv2.destroyAllWindows()  # Pencereler kapatılır