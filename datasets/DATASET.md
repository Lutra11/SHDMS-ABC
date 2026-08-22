# NST‑HSR Dataset Description

The self‑constructed **NST‑HSR dataset** targets the Nanjing South‑Taicang section of the Nanjing‑Yancheng Riverside High‑Speed Railway. Basic operational information including train schedules, adjacent station pairs, planned arrival/departure timestamps, section distances, tracking intervals and fares are compiled from publicly available information released by China Railway 12306. Station locations, platform and line capacity parameters are constructed based on public line/station documents and capacity parameter tables derived from existing research.

The main dataset contains **390 adjacent‑station segment records**, **204 unique train services**, and **9 stations**, with a calculated route length of 275 km. For this paper, 382 records within the time window of 06:00–22:00 are adopted and further divided into six time periods.

## Dataset File Overview

| File Name                | Granularity               | Purpose                                    | Number of Fields |
| ------------------------ | ------------------------- | ------------------------------------------ | ---------------- |
| `*-Timetable.xlsx`       | Train‑segment level       | Timetables and extended attributes         | 41               |
| `*-Factors.xlsx`         | Station‑time‑period level | Passenger demand and traveller composition | 11               |
| `Platform Capacity.xlsx` | Station level             | Capacity and constraint parameters         | 8                |

## Supplementary Generalization‑Oriented Datasets

The `Supplement` folder contains extended experimental datasets built following the identical three‑file structure and unified specification of NST‑HSR for generalization tests. These supplementary datasets cover four representative intercity/metropolitan‑rail routes:
1. Xincheng Express (Wuhan East‑Daye North / Huanggang West / Xianning South)
2. Wuhan‑Xiaogan Intercity Railway (Hankou‑Xiaogan East)
3. Guangzhou‑Shenzhen Intercity Railway (Xintang South‑Shenzhen Airport)
4. Beijing Sub‑Center Railway (Liangxiang‑Beijing West‑Qiaozhuang East)

Route terminals, station sequences and mileages for these supplementary datasets are compiled from public open‑source materials.

## Dataset Download Link
Google Drive: <https://drive.google.com/drive/folders/1mYckg3XB5ZU7fgRFuytrwnFazu1uvmuG>





