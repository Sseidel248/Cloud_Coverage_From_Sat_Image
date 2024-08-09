# Cloud_Coverage_From_Sat_Image
Read out the degree of sky coverage from a specific satellite image. The Mercator projection is used to convert the coordinate into pixels.

# What you need?
- One or more images of the same size in the same area
- Size of the image
- Area of the earth to be covered (longitude and latitude)

# How to optimize the grey threshold?
With a set of satellite images and DWD station data a grey value optimization can be performed. 
The default gray value is: 160

Required for the optimization:
Some File of the following project:
[Cloud-coverage-estimation](https://github.com/Sseidel248/Cloud-coverage-estimation)
- [Grib2Reader.py](https://github.com/Sseidel248/Cloud-coverage-estimation/blob/main/Lib/Grib2Reader.py)
- [DWDStationReader.py](https://github.com/Sseidel248/Cloud-coverage-estimation/blob/main/Lib/DWDStationReader.py)
- [IOConst.py](https://github.com/Sseidel248/Cloud-coverage-estimation/blob/main/Lib/IOConsts.py)
- [GeneralFunctions.py](https://github.com/Sseidel248/Cloud-coverage-estimation/blob/main/Lib/GeneralFunctions.py)

# Required Python Packages
| Package      | Version      |
|--------------|--------------|
| colorama     | 0.4.6        |
| matplotlib   | 3.8.2        |
| numpy        | 1.26.2       |
| pandas       | 2.1.4        |
| pillow       | 10.1.0       |
| requests     | 2.31.0       |
| tqdm         | 4.66.1       |
