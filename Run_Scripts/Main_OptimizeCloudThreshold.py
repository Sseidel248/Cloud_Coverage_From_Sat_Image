from datetime import datetime
from pathlib import Path
from Lib import DWDStationReader as dwd
from Lib.IOConsts import COL_LAT, COL_LON, COL_DWD_LOADED
from PIL import Image
from tqdm import tqdm
import numpy as np


def latlon_to_pixel(lat, lon, width, height):
    # Mercator Projektion
    # Berechne die x-Koordinate (Longitude)
    pix_x = (lon - min_lon) / (max_lon - min_lon) * width

    # Berechne die y-Koordinate (Latitude) unter Verwendung der Mercator-Projektion
    lat_rad = np.radians(lat)
    min_lat_rad = np.radians(min_lat)
    max_lat_rad = np.radians(max_lat)
    pix_y = (np.log(np.tan(np.pi / 4 + lat_rad / 2)) - np.log(np.tan(np.pi / 4 + min_lat_rad / 2))) / \
            (np.log(np.tan(np.pi / 4 + max_lat_rad / 2)) - np.log(np.tan(np.pi / 4 + min_lat_rad / 2))) * height

    # Pixelkoordinaten umdrehen, da y in Bildern von oben nach unten geht
    return int(pix_x), int(height - pix_y)


def calculate_column_means(arr):
    # Leeres Array für die Mittelwerte
    column_means = []
    # Schleife über jede Spalte
    for arr_col in range(arr.shape[1]):
        # Extrahiere die Spalte
        column_data = arr[:, arr_col]
        # Berechne den Mittelwert, wenn die Spalte keine nur NaN-Werte enthält
        if np.isnan(column_data).all():
            column_means.append(np.NaN)
        else:
            column_mean = np.nanmean(column_data)
            column_means.append(column_mean)
    return column_means


# Definieren des Zeitraums der Optimiert werden soll, als Quelle hier dienen die Sat-Bilder
dates = []
imgs = list(Path(f"../combined_images/germany\\").glob(f"**/*.jpg"))
if len(imgs) == 0:
    raise ValueError("Es exierieren keine Bilder in: '.\\combined_images\\germany\\'")

# Jedes Bild steht für ein Datum und Uhrzeit, d.h. Anzahl dates = Anzahl Bilder
for path in imgs:
    # Dateiendung entfernen und den Dateinamen als Datetime-Objekt umwandeln
    file = Path(path)
    dt = datetime.strptime(file.stem, "%Y%m%d_%H%M_UTC")
    dates.append(dt)

# Referenz laden und Koordinaten holen
dwd_data = dwd.DWDStations()
dwd_data.load_folder(".\\DWD_Stations")
# lese nur die geladenen Einträge aus
valid_entries = dwd_data.df[dwd_data.df[COL_DWD_LOADED].astype(bool)]
coords = list(zip(valid_entries[COL_LAT], valid_entries[COL_LON]))

# Referenzen als numpy Array befüllen
ref_dwd_values = np.full((len(dates), len(coords)), np.NaN)
for col, (a_lat, a_lon) in tqdm(enumerate(coords), total=len(coords), desc="Referenzwerte der DWD-Stationen auslesen"):
    res = dwd_data.get_values(dates, a_lat, a_lon)
    if not res.empty:
        # sicherstellen, dass die Einfügeindizes nicht über die Grenzen gehen
        num_values_to_fill = min(len(dates), len(res))
        ref_dwd_values[:num_values_to_fill, col] = res["V_N"][:num_values_to_fill]
ref_dwd_values = (ref_dwd_values / 8) * 100

# Hole Abmaße der Bilder
tmp_img = Image.open(imgs[0])
img_height, img_width = tmp_img.size

# Grenzen des Bildes setzen - Ablesen anhand eines Bildes und OpenStreetMap
min_lon, max_lon = 5.632, 16.887
min_lat, max_lat = 45.129, 55.772

# Radius der Erde
earth_radius = 6371

# Elemente von coords in Pixel umwandeln
pxls = []
for a_lat, a_lon in tqdm(coords, total=len(coords), desc="Koordinaten in Pixel umwandeln"):
    # y_tmp, x_tmp = _gps_to_pixel(a_lat, a_lon, trans_mat)
    y_tmp, x_tmp = latlon_to_pixel(a_lat, a_lon, img_width, img_height)
    pxls.append((y_tmp, x_tmp))

# Für jedes Pixel die Werte mit Radius = 4 Pixel holen und den Mittelwert davon bilden
radius = 4
mean_gray_pxl_date = np.zeros((len(imgs), len(pxls)))
for row, path in tqdm(enumerate(imgs), total=len(imgs), desc="Pixel aus den Bildern auslesen"):
    tmp_img = Image.open(path)
    tmp_grayscale_img = tmp_img.convert("L")
    tmp_img_arr = np.array(tmp_grayscale_img)
    for col, (y, x) in enumerate(pxls):
        region = tmp_img_arr[y - radius:y + radius, x - radius:x + radius]
        if not region.size == 0:
            mean_gray_pxl_date[row, col] = np.mean(region)
        else:
            mean_gray_pxl_date[row, col] = np.NaN

if mean_gray_pxl_date.shape != (len(dates), len(pxls)):
    raise ValueError(f"Fehler beim Erzeugen vom mean_gray_pxl_date-Array.\n"
                     f"Erwartetes Shape: {(len(dates), len(pxls))}\n"
                     f"Bekommenes Shape: {mean_gray_pxl_date.shape}")

# Definieren der zu prüfenden Graugrenzwerte zur Wolkenerkennung
gray_thresholds = range(1, 256)

# Berechnete Bereiche der Grauwerte mit dem jeweiligen Grenzwert normieren
# all_mean_thresholds = np.zeros((len(gray_thresholds), len(pxls)))
all_mean_thresholds = np.full((len(gray_thresholds), len(pxls)), np.NaN)
norm_gray_pxl = np.zeros(mean_gray_pxl_date.shape)
for row, threshold in tqdm(enumerate(gray_thresholds), total=len(gray_thresholds), desc="Grauwertoptimierung"):
    if threshold != 0:
        norm_gray_pxl = (mean_gray_pxl_date / threshold) * 100
    norm_gray_pxl[norm_gray_pxl > 100] = 100
    # Differenz zwischen Referenz und SatBilder berechnen
    diff_arr = norm_gray_pxl - ref_dwd_values
    pot_arr = diff_arr ** 2
    # Enferne alle Zeilen, die nur aus NaN bestehen
    non_nan_rows = ~np.isnan(pot_arr).all(axis=1)
    filtered_arr = pot_arr[non_nan_rows]
    all_mean_thresholds[row, :] = calculate_column_means(filtered_arr)
    # nicht np.nanmean(...) verwenden, da es Spalten mit Nan geben kann und es dann eine RuntimeWarning erzeugt
    # all_mean_thresholds[row, :] = np.nanmean(filtered_arr, axis=0)

if all_mean_thresholds.shape != (len(gray_thresholds), len(pxls)):
    raise ValueError(f"Fehler beim Erzeugen vom all_mean_thresholds-Array.\n"
                     f"Erwartetes Shape: {(len(gray_thresholds), len(pxls))}\n")

# Mittelwert von allen ermittelten Grauwerte der Koordinaten bilden, zeilenweise
final_result = np.nanmean(all_mean_thresholds, axis=1)

print(f"Gemittelte Idealwert für alle Koordinaten: {gray_thresholds[np.argmin(final_result)]}")
