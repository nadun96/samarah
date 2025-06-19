import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
import re
import time
import random


headers = {
    ":authority": "jurnal.ar-raniry.ac.id",
    ":method": "POST",
    ":path": "/index.php/samarah/announcement",
    ":scheme": "https",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,si;q=0.8",
    "cache-control": "max-age=0",
    "content-length": "4995",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "HstCfa4473498=1750162142755; HstCmu4473498=1750162142755; __dtsu=51A01740039281B7194034E9DC494DA8; _cc_id=58b2be828e51571f94b5fdc6dda53b23; panoramaId=de2490231d19d03b1621f6fd145f16d53938aa3e23cf56160942c0716a9798f2; panoramaIdType=panoIndiv; OJSSID=r5hfpmsnnai42qds61u82qedr2; HstCnv4473498=4; panoramaId_expiry=1750910723945; HstCla4473498=1750306586622; HstPn4473498=9; HstPt4473498=29; HstCns4473498=8; cf_clearance=LbHNF2lbKJByyic6vETHKXS6GLZ6jKJpd9fAHYPGJSU-1750306769-1.2.1.1-5l_ogmo9.hAaV.tZm3B2dhBJev0vMRc7s6xNRIfdotQIPe94Yrmc32Rrka5fuzcJiV.oqEw6PsSBq_Je5wUyNfVKiEvL16Rfzhiq_2HwODm4YZ1AEVrF0PmkWhlTziv35ZU9G_ZunD_r1D6RvuNWb4cpGUg72iCxo4J5.gOXOiN21x2xac8gJxnljnEEvT2Qp0Sindqk0fqy1Uuo4XwqXknQ2cn1e6Qea.A1XZDQ9rd0wEA98HcSf1j4qPwdfhzPhqZ23QXOQN9ZX97P23YxbE5N44BN5t0RgR4eEIYSoaO2fP4ZuCOK_A9SytsNVCS1OYE4_320bBKx6W18emcm9ZPWRFMKRjvbYhjbkjqOzxS54gzmQcI4xx5pjyb9P",
    "origin": "https://jurnal.ar-raniry.ac.id",
    "priority": "u=0, i",
    "referer": "https://jurnal.ar-raniry.ac.id/index.php/samarah/announcement?__cf_chl_tk=SUhPLEOkBBaBX3BVY5Kfact0jIhQ9JSmfUzBbLmVcVo-1750306730-1.0.1.1-wvy4XTRvWMaDZbddWCIjvi_Z6wR6Ee6ePj_VnewE82I",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-arch": '""',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": "137.0.7151.105",
    "sec-ch-ua-full-version-list": '"Google Chrome";v="137.0.7151.105", "Chromium";v="137.0.7151.105", "Not/A)Brand";v="24.0.0.0"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-model": '"Nexus 5"',
    "sec-ch-ua-platform": '"Android"',
    "sec-ch-ua-platform-version": "6.0",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
}


