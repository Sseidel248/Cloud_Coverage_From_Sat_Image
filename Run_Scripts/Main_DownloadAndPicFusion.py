import pandas as pd
import requests
import os
import numpy as np
from PIL import Image
from pathlib import Path
from tqdm import tqdm
from datetime import datetime, timezone, time


def get_subdirectories(directory):
    subdirectories = [d.name for d in os.scandir(directory) if d.is_dir()]
    return subdirectories


def check_shape(lst, shape):
    arr = np.array(lst)
    return arr.shape == shape


def get_rounded_unix_timestamp(dt: datetime | str):
    if isinstance(dt, str):
        conv_date = datetime.strptime(dt, "%Y%m%d%H")
    else:
        conv_date = dt
    # Minuten auf den nächsten niedrigeren 5-Minuten-Wert runden
    rounded_minute = (conv_date.minute // 5) * 5

    # Neue Zeit erstellen, gerundet auf die letzte 5-Minuten-Marke
    rounded_time = conv_date.replace(minute=rounded_minute, second=0, microsecond=0)

    # Unix-Zeitstempel der gerundeten Zeit berechnen
    unix_timestamp = int(rounded_time.timestamp())
    return unix_timestamp


# ---- Download der Teilbilder + Teil 1/2 ---- #
start_time = datetime.combine(datetime.now().date(), time(7, 0))
end_time = datetime.combine(datetime.now().date(), time(19, 0))
date_range = pd.date_range(start_time, end_time, freq="H")
dates_str = [date.strftime("%Y%m%d%H") for date in date_range]

# Webseite, die analysiert werden soll
url = "https://www.daswetter.com/satelliten/"

# Verzeichnis, in dem die Bilder gespeichert werden sollen
output_dir = "../downloaded_images"

# definieren welche Server es gibt
service_c_meteored = "https://services-c.meteored.com/"
service_b_meteored = "https://services-b.meteored.com/"
service_a_meteored = "https://services-a.meteored.com/"

# List mit Daten in Unixzeitstempel umformen
dates = []
for date_str in dates_str:
    dates.append(get_rounded_unix_timestamp(date_str))

# Erstelle das Verzeichnis, falls es nicht existiert
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

services = [service_a_meteored, service_b_meteored, service_c_meteored]

for date in tqdm(dates, total=len(dates), desc=f"Download der Teilbilder für jedes Datum"):
    list_xy = []
    num_of_pics = 0
    for service in services:
        new_url = f"{service}img/tiles/viewer/satellite/6"

        # Bildname und Verzeichnisstruktur
        img_name = f"{date}_rgb.jpg"
        save_dir = os.path.join(output_dir, f"{date}")

        germany_y_map = [20, 21, 22]
        germany_x_map = [33, 34]
        if num_of_pics == len(germany_y_map) * len(germany_x_map):
            continue

        germany_xy_map = [(f"{new_url}/{x}/{y}/{img_name}", f"{x}/{y}") for y in germany_y_map for x in germany_x_map]

        # Bild herunterladen
        for link, xy in germany_xy_map:
            if xy in list_xy:
                continue
            try:
                img_response = requests.get(link)
                img_response.raise_for_status()

                img_folder = os.path.abspath(os.path.join(save_dir, xy))
                # Verzeichnis erstellen, falls nicht vorhanden
                if not os.path.exists(img_folder):
                    os.makedirs(img_folder)
                img_path = os.path.abspath(os.path.join(img_folder, img_name))

                with open(img_path, "wb") as img_file:
                    img_file.write(img_response.content)

                list_xy.append(xy)
                num_of_pics += 1
                # print(f"Bild {link} heruntergeladen und gespeichert.")
            except requests.exceptions.RequestException as e:
                print(f"Fehler beim Herunterladen von {link}: {e}")

# ---- Bilder Fusion der Teilbilder + Teil 2/2 ---- #
# bestimme die Anzahl der Zeilen und Spalten
m = 2  # Anzahl der Spalten
n = 3  # Anzahl der Zeilen
positions = [(0, 1, 2), (3, 4, 5)]  # 2x3 Beispiel, passen Sie dies entsprechend an
target_dir = "germany"
save_dir = "../combined_images"

if not check_shape(positions, (m, n)):
    raise ValueError(f"positions muss das Format m x n haben. Aktuell: ({m}, {n})")

# Pfad zu den Bildern
img_folders = get_subdirectories(output_dir)
for img_folder in tqdm(img_folders, total=len(img_folders), desc=f"Bilderfusion von {output_dir}"):
    image_directory = os.path.abspath(os.path.join(output_dir, img_folder))
    save_path = os.path.abspath(os.path.join(save_dir, target_dir))

    # Definiere die Bilddateien und ihre Positionen
    pathes = list(Path(image_directory).glob(f"**/*.jpg"))
    image_files = [str(path) for path in pathes]

    # Lade die Bilder
    images = [Image.open(os.path.join(image_directory, file)) for file in image_files]

    # Nimm an, alle Bilder haben die gleiche Größe
    width, height = images[0].size

    # Bestimme die Größe des größeren Bildes
    new_width = m * width
    new_height = n * height

    # Erstelle ein neues, leeres Bild
    new_image = Image.new("RGB", (new_width, new_height))

    # Füge die Bilder an den definierten Positionen ein
    idx = 0
    for col, position in enumerate(positions):
        for row, _ in enumerate(position):
            r = row % n  # Zeilenindex
            c = col % m  # Spaltenindex
            x = col * width
            y = row * height
            new_image.paste(images[idx], (x, y))
            idx += 1

    # Speichere das neue Bild
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    date = datetime.fromtimestamp(int(img_folder))
    date_utc = date.astimezone(timezone.utc)
    img_name = date_utc.strftime("%Y%m%d_%H%M_UTC")

    img_path = os.path.abspath(f"{save_path}\\{img_name}.jpg")
    new_image.save(img_path)
