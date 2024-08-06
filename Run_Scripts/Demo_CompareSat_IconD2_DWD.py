from Lib.SatImgReader import SatImgReader
from datetime import datetime
from Lib import DWDStationReader as dwd
from Lib import Grib2Reader as gr
from Lib import IOConsts as ioc
from pathlib import Path
import numpy as np


# Testzeitraum und Testkoordinate bestimmen
test_coord = (52.4537, 13.3017)
dates = []
imgs = list(Path(f"../combined_images/germany\\").glob(f"**/*.jpg"))
if len(imgs) == 0:
    raise ValueError("No images are exported in: '.\\combined_images\\germany\\'")
for path in imgs:
    # Dateiendung entfernen und den Dateinamen als Datetime-Objekt umwandeln
    file = Path(path)
    dt = datetime.strptime(file.stem, "%Y%m%d_%H%M_UTC")
    dates.append(dt)

# Laden der Sat.-Bilder
sat_reader = SatImgReader(f"../combined_images/germany\\")
sat_reader.initialize(own_threshold=197)  # 2024.07.22
result_test2 = sat_reader.get_cloud_coverage(dates, test_coord)
# print(result_test2)

# Laden der Grib2 Dateien
g2r = gr.Grib2Datas()
g2r.load_folder(".\\icon_d2")
g2r_result = g2r.get_values(ioc.MODEL_ICON_D2, ioc.CLOUD_COVER, dates, test_coord)
# print(g2r_result)

# Laden der DWD-Stationsdateien
dwd_data = dwd.DWDStations()
dwd_data.load_folder(".\\DWD_Stations")
lat, lon = test_coord
dwd_result = dwd_data.get_values(dates, lat, lon)
# print(dwd_result)

# Ergebnisse zusammenfügen
result_test2["ICON_D2_TCDC"] = g2r_result[ioc.CLOUD_COVER]
result_test2["DWD_CloudCoverage"] = (dwd_result["V_N"].astype(int) / 8) * 100
# print(result_test2.to_string())

# Mittleren absoluten Fehler zwischen den Quellen mit DWD-Station als Referenz berechnen
mae = np.mean(np.abs(result_test2["ICON_D2_TCDC"] - result_test2["DWD_CloudCoverage"]))
print(f"Mean Absolute Error (MAE) [Cloud Coverage] ICON-D2 and DWD-Stations: {mae:.2f} %")
mae = np.mean(np.abs(result_test2["Cloud_Coverage"] - result_test2["DWD_CloudCoverage"]))
print(f"Mean Absolute Error (MAE) [Cloud Coverage] Sat.Bilder and DWD-Stations: {mae:.2f} %")
