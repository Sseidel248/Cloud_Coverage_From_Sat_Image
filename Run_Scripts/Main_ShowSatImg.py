from Lib.SatImgReader import *
from PIL import Image
from matplotlib import pyplot as plt
import numpy as np


# Funktion zur Umwandlung von Koordinaten in Pixel
def latlon_to_pixel(img, lon, lat):
    # ---> Funktion aus SatImReader kopiert <---

    width, height = img.size
    # Mercator Projektion
    # Berechne die x-Koordinate (Longitude)
    x = (lon - MIN_LON_GER) / (MAX_LON_GER - MIN_LON_GER) * width

    # Berechne die y-Koordinate (Latitude) unter Verwendung der Mercator-Projektion
    lat_rad = np.radians(lat)
    min_lat_rad = np.radians(MIN_LAT_GER)
    max_lat_rad = np.radians(MAX_LAT_GER)
    y = (np.log(np.tan(np.pi / 4 + lat_rad / 2)) - np.log(np.tan(np.pi / 4 + min_lat_rad / 2))) / \
        (np.log(np.tan(np.pi / 4 + max_lat_rad / 2)) - np.log(np.tan(np.pi / 4 + min_lat_rad / 2))) * height

    # Pixelkoordinaten umdrehen, da y in Bildern von oben nach unten geht
    return int(x), int(height - y)


# Darstellen aller DWD-Stationen auf einem Satellitenbild
# dwd_data = dwd.DWDStations()
# dwd_data.load_folder(".\\DWD_Stations")
# show_poses = list(zip(dwd_data.df[COL_LAT], dwd_data.df[COL_LON]))
show_poses = [(52.519683856228305, 13.40824400801289),
              (54.82094893832346, 9.45336095833125),
              (47.568693047361656, 10.699923350545903),
              (51.05061896926067, 5.905757455655236),
              (50.60682981164014, 10.689812285349753)]

# Beispiel Bild laden
img_name = "20240724_1200_UTC.jpg"
tmp_img = Image.open(f".\\combined_images\\germany\\{img_name}")
image_np = np.array(tmp_img)

# Koordinaten in Pixel umwandeln
img_x, img_y = [], []
for _lat, _lon in show_poses:
    tmp_x, tmp_y = latlon_to_pixel(tmp_img, _lon, _lat)
    img_x.append(tmp_x)
    img_y.append(tmp_y)

# Umgewandelte Pixelkoordinaten plotten
plt.imshow(image_np)
plt.scatter(img_x, img_y,
            color="red",
            marker="x")
plt.title(f"GPS coordinates on the image of: {img_name}")
plt.axis("off")  # Achsen ausschalten
plt.show()
