import os.path
import numpy as np
from PIL import Image
from pathlib import Path
from matplotlib import pyplot as plt
from pandas import DataFrame
from datetime import datetime
from typing import List, Tuple
from numpy.typing import NDArray


COL_DATE: str = "Date_UTC"
COL_FILE: str = "Filename"
COL_LAT: str = "Lat"
COL_LON: str = "Lon"
COL_CLOUDCOV: str = "Cloud_Coverage"

# Grenzen des Bildes setzen - Ablesen anhand eines Bildes und OpenStreetMap - Deutschland
MIN_LON_GER, MAX_LON_GER = 5.632274467934759, 16.88723585646731
MIN_LAT_GER, MAX_LAT_GER = 45.12897716888877, 55.77161130134562


class SatImgReader:
    def __init__(self,
                 path: str):
        pathes = list(Path(path).glob(f"**/*.jpg"))
        cols = [COL_DATE, COL_FILE]
        dates = []
        files = []
        self.df: DataFrame = DataFrame(columns=cols)
        for path in pathes:
            file = Path(path)
            date = datetime.strptime(file.stem, "%Y%m%d_%H%M_UTC")
            dates.append(date)
            files.append(os.path.abspath(path))
        self.df[COL_DATE] = dates
        self.df[COL_FILE] = files
        self.cloud_threshold = 160
        self.img_min_lat = 0
        self.img_max_lat = 0
        self.img_min_lon = 0
        self.img_max_lon = 0
        self.img_height = 0
        self.img_width = 0
        if not pathes:
            raise ValueError(f"There are no images (*.jpg) in:{path}")
        else:
            tmp_img = Image.open(pathes[0])
            self.img_height, self.img_width = tmp_img.size

    def initialize(self,
                   min_lat: float = MIN_LAT_GER,
                   max_lat: float = MAX_LAT_GER,
                   min_lon: float = MIN_LON_GER,
                   max_lon: float = MAX_LON_GER,
                   own_threshold: int = 160):
        self.cloud_threshold = abs(own_threshold)
        self.img_min_lat = min_lat
        self.img_max_lat = max_lat
        self.img_min_lon = min_lon
        self.img_max_lon = max_lon

    def _latlon_to_pixel(self, lat, lon):
        """
        Mercator-Projektion für einen bestimmten Bereich

        Wird die Breite und Höhe der Karte (width und height) genutzt, um die Koordinaten zu skalieren,
        entfällt die Notwendigkeit der expliziten Berücksichtigung des Erdradius. Die Koordinaten werden
        innerhalb der gegebenen Grenzen (MIN_LON_GER, MAX_LON_GER, MIN_LAT_GER, MAX_LAT_GER) auf die Dimensionen der
        Karte abgebildet. Das bedeutet, dass der Erdradius implizit durch die Dimensionen und die Skalierung der
        Karte berücksichtigt wird.
        """
        # Mercator Projektion
        # Berechne die x-Koordinate (Longitude)
        pix_x = (lon - self.img_min_lon) / (self.img_max_lon - self.img_min_lon) * self.img_width

        # Berechne die y-Koordinate (Latitude) unter Verwendung der Mercator-Projektion
        lat_rad = np.radians(lat)
        min_lat_rad = np.radians(self.img_min_lat)
        max_lat_rad = np.radians(self.img_max_lat)
        pix_y = (np.log(np.tan(np.pi / 4 + lat_rad / 2)) - np.log(np.tan(np.pi / 4 + min_lat_rad / 2))) / \
                (np.log(np.tan(np.pi / 4 + max_lat_rad / 2)) - np.log(np.tan(np.pi / 4 + min_lat_rad / 2))) * self.img_height

        # Pixelkoordinaten umdrehen, da y in Bildern von oben nach unten geht
        return int(pix_x), int(self.img_height - pix_y)

    def show_image(self, date: datetime, lat: float, lon: float):
        if self.img_min_lat == self.img_max_lat == self.img_min_lon == self.img_max_lon:
            raise ValueError(f"The initialize(...) function of SatPicReader was forgotten to be called.")
        img_x, img_y = self._latlon_to_pixel(lat, lon)

        img_entry = self.df[self.df[COL_DATE] == date]
        if img_entry.empty:
            raise ValueError(f"No Image for {date} exists.")
        tmp_img = Image.open(img_entry[COL_FILE].iloc[0])
        image_np = np.array(tmp_img)
        plt.imshow(image_np)
        plt.scatter(img_x, img_y, color="red", marker="o", s=50, linewidths=1, facecolors="none", edgecolors="black")
        plt.title(f"GPS coordinate {(lat, lon)} on the image from: {date}")
        plt.axis("off")  # Achsen ausschalten
        plt.show()

    def get_cloud_coverage(self,
                           datetimes: datetime | List[datetime],
                           coords: Tuple[float, float] | List[Tuple[float, float]]
                           ) -> DataFrame:

        def get_width_len(arr: NDArray) -> Tuple[int, int]:
            # len(arr) == 1 then there is no second value
            if len(arr.shape) == 1:
                return arr.shape[0], 1
            else:
                return arr.shape[1], arr.shape[0]

        def conv_to_np(data, dtype: str):
            if not isinstance(data, list):
                data = [data]
            return np.array(data, dtype=dtype)

        np_datetimes = conv_to_np(datetimes, "datetime64[m]").reshape(-1, 1)
        np_coords = conv_to_np(coords, "float64")

        coords_width, coords_len = get_width_len(np_coords)
        datetimes_width, datetimes_len = get_width_len(np_datetimes)

        if coords_width != 2:
            raise ValueError(f"The parameter 'coords' has an incorrect dimensioning. Shape must be (n, 2).")

        if datetimes_len != coords_len:
            if datetimes_len == 1:
                np_datetimes = np.full((coords_len, 1), np_datetimes[0])
            if coords_len == 1:
                np_coords = np.full((datetimes_len, 2), np_coords)
            if datetimes_len > 1 and coords_len > 1:
                raise ValueError(f"Only one parameter may have a length of 1. "
                                 f"Coords must be (n, 2) and 'date_times' must be (n, 1)")

        if self.img_min_lat == self.img_max_lat == self.img_min_lon == self.img_max_lon:
            raise ValueError(f"The initialize(...) function of SatPicReader was forgotten to be called.")

        cols = [COL_DATE, COL_LAT, COL_LON, COL_CLOUDCOV]
        result_df: DataFrame = DataFrame(columns=cols)

        # TODO: Runden auf ganze 5 Minuten - datetimes
        # TODO: doppelte wegschmeißen

        for idx, date in enumerate(np_datetimes):
            lat, lon = np_coords[idx]

            # Minuten auf den nächsten niedrigeren 5-Minuten-Wert runden
            a_date = date[0].astype(datetime)
            rounded_minute = (a_date.minute // 5) * 5
            # Neue Zeit erstellen, gerundet auf die letzte 5-Minuten-Marke
            rounded_date = a_date.replace(minute=rounded_minute, second=0, microsecond=0)
            entry = self.df[self.df[COL_DATE] == rounded_date]
            if entry.empty:
                new_row = {
                    COL_DATE: date,
                    COL_LAT: lat,
                    COL_LON: lon,
                    COL_CLOUDCOV: np.NaN
                }
            else:
                # Passendes Bild laden
                filename = entry[COL_FILE].iloc[0]
                img = Image.open(filename)
                grayscale_image = img.convert("L")
                img_arr = np.array(grayscale_image)
                # Gps zu Pixel konvertieren
                y, x = self._latlon_to_pixel(lat, lon)
                # Radius 1 entspricht etwa 3 km - so wie die Auflösung der Satelliten
                radius = 4
                region = img_arr[y - radius:y + radius, x - radius:x + radius]
                if self.cloud_threshold > 0:
                    cloud_coverage = np.mean(region) / self.cloud_threshold  # 255 wäre reines weiß
                else:
                    cloud_coverage = 0
                # Wert auf 1, also 100 % beschränken
                if cloud_coverage > 1:
                    cloud_coverage = 1
                # neuen Eintrag vorbereiten
                new_row = {
                    COL_DATE: date,
                    COL_LAT: lat,
                    COL_LON: lon,
                    COL_CLOUDCOV: cloud_coverage * 100
                }
            # Werte dem Rückgabe-DataFrame hinzufügen
            result_df.loc[len(result_df)] = new_row
        return result_df
