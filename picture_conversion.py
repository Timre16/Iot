import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import zscore

# Bild laden
image_path = "C:/Users/timei/Pictures/final_presentation/AIR_INITIAL.png"
image = cv2.imread(image_path)

# In den HSV-Farbraum umwandeln
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Farbmaske für Blau erstellen (Graph-Farbe)
lower_blue = np.array([100, 50, 50])
upper_blue = np.array([140, 255, 255])
mask = cv2.inRange(hsv, lower_blue, upper_blue)

# Maske auf das Originalbild anwenden
result = cv2.bitwise_and(image, image, mask=mask)

# In Graustufen umwandeln
gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
_, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

# Konturen finden
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Pixel-Koordinaten extrahieren
extracted_points = [(point[0][0], point[0][1]) for contour in contours for point in contour]

# Filterung der Legende (genauere Begrenzung)
legend_x_min_threshold = image.shape[1] * 0.6  # 60% der Bildbreite von links
legend_x_max_threshold = image.shape[1] * 0.9  # 90% der Bildbreite von links
legend_y_min_threshold = image.shape[0] * 0.0  # 0% der Bildhöhe von oben
legend_y_max_threshold = image.shape[0] * 0.3   # 30% der Bildhöhe von oben

# Extrahieren der Punkte, die sich nicht im Bereich der Legende befinden
extracted_points = [
    (x, y) for x, y in extracted_points 
    if not (legend_x_min_threshold <= x <= legend_x_max_threshold and 
            legend_y_min_threshold <= y <= legend_y_max_threshold)
]

# Nach X-Koordinate sortieren
extracted_points = sorted(extracted_points, key=lambda p: p[0])

# In numpy-Arrays umwandeln
pixels_x = np.array([p[0] for p in extracted_points])
pixels_y = np.array([p[1] for p in extracted_points])

# Achsenlimits bestimmen
x_pixel_min, x_pixel_max = min(pixels_x), max(pixels_x)
y_pixel_min, y_pixel_max = min(pixels_y), max(pixels_y)

# Echte Achsenwerte
x_freq_min, x_freq_max = 1.2, 2.0  # Frequenz in GHz
y_s11_min, y_s11_max = -10.5, -1.2 # dB-Bereich

# Skalierung der X-Werte (Frequenz)
freq_values = x_freq_min + (pixels_x - x_pixel_min) * (x_freq_max - x_freq_min) / (x_pixel_max - x_pixel_min)

# **Korrekte Skalierung der Y-Werte (dB: invertierte Y-Achse in Bildern!)**
s11_values = y_s11_max - (pixels_y - y_pixel_min) * (y_s11_max - y_s11_min) / (y_pixel_max - y_pixel_min)


# Ergebnisse plotten
plt.figure(figsize=(8,6))
plt.plot(freq_values, s11_values, 'r.', markersize=2, label="Extrahierte Daten")
plt.xlabel("Frequenz (GHz)")
plt.ylabel("S11 (dB)")



plt.legend()
plt.grid()
plt.show()

# Speichern der extrahierten Daten als TXT
np.savetxt("C:/Users/timei/Desktop/Graph.txt", np.column_stack((freq_values, s11_values)), 
           delimiter="\t", comments='', fmt="%.13f")
