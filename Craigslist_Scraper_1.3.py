import argparse
import email.message
import json
import os
import random
import smtplib
import time
import traceback

import requests
from bs4 import BeautifulSoup

smtp_email = 'sales@unixcommerce.com'
smtp_pass = 'kymbte'
smtp_host = 'smtp.gmail.com'
smtp_port = 587
receiver_address = 'sales@unixcommerce.com'
sent = []
if os.path.isfile("sent.txt"):
    with open("sent.txt", "r") as f:
        sent = f.read().splitlines()
api = "https://sapi.craigslist.org/web/v7/postings/search/full"
proxies = []
if os.path.isfile("proxies.txt"):
    with open("proxies.txt", "r") as f:
        proxies = f.read().splitlines()
else:
    print("No proxies.txt file found!")
    time.sleep(3)
sleep_time_min = 5
sleep_time_max = 10


def processState(state):
    url = f"https://{state}.craigslist.org/search/bbb"
    print(f"Working on {url}")
    print(getRequest('http://lumtest.com/myip.json').text)
    soup = getSoup(url)
    try:
        ul = soup.find('ul', attrs={'id': 'search-results'})
        if ul is not None:
            links = ul.find_all('a', {'data-id': True})
            for link in links:
                href = link.get('href')
                if href is not None:
                    sendmail(href)
        else:
            print(f"{state} is API based!")
            getApiBasedUrl(state)
    except:
        traceback.print_exc()
        print(soup.text)
    for i in range(random.randint(sleep_time_min, sleep_time_max)):
        print(f"Sleeping for {sleep_time_max - i} seconds")
        time.sleep(1)


def getApiBasedUrl(state):
    area_id = state_area_id[state]
    params = {
        'batch': f'{area_id}-0-360-0-0',
        'cc': 'US',
        'lang': 'en',
        'searchPath': 'bbb'
    }
    val = getJson(params)
    # print(json.dumps(val, indent=4,ensure_ascii=False))
    ret_posts = {}
    if not val['data']['totalResultCount']:
        return ret_posts
    min_post_id = val['data']['decode']['minPostingId']
    loc_list = val['data']['decode']['locations']
    for i in val['data']['items']:
        meta_str = i[4]
        posting_id = i[0] + min_post_id
        posting_cat = categories[f"{i[2]}"]
        # area_id, hostname, subarea_abbr = get_area_tup(loc_list, meta_str)
        tup = get_area_tup(loc_list, meta_str)
        if len(tup) == 3:
            area_id, hostname, subarea_abbr = tup
            url = f'https://{hostname}.craigslist.org/{subarea_abbr}/{posting_cat}/{posting_id}.html'
        else:
            area_id, hostname = tup
            url = f'https://{hostname}.craigslist.org/{posting_cat}/{posting_id}.html'
        sendmail(url)


def get_area_tup(loc_list, meta_string):
    # ret = loc_list[int(meta_string.split('~')[0].split(":")[0])]
    # if len(ret) == 2:
    #     return *ret, None
    # else:
    # print(f"Getting area tuple for loc_list {loc_list}, meta_string {meta_string}")
    return loc_list[int(meta_string.split('~')[0].split(":")[0])]


def main():
    logo()
    states = []
    if os.path.isfile("cities.txt"):
        with open("cities.txt", "r") as sfile:
            states = sfile.read().splitlines()
    for state in states:
        processState(state)


def sendmail(url):
    if url in sent:
        print(f"Already sent {url}")
        return
    res = getRequest(url)
    if "ok to contact this poster with services or other commercial interests" in res.text:
        for i in range(5):
            try:
                print(f"Sending {url}")
                message = email.message.Message()
                message['From'] = smtp_email
                message['To'] = receiver_address
                message['Subject'] = 'Craigslist Ok to Contact'
                message.add_header('Content-Type', 'text/html')
                message.set_payload('Matched Url<br> <a href={}>{}</a>')
                session = smtplib.SMTP(smtp_host, smtp_port)
                session.starttls()
                session.login(smtp_email, smtp_pass)
                session.sendmail(smtp_email, receiver_address, message.as_string().format(url, url))
                session.quit()
                sent.append(url)
                with open("sent.txt", "a") as s:
                    s.write(f"{url}\n")
                break
            except:
                traceback.print_exc()
    elif "do NOT contact me with unsolicited services or offers" in res.text:
        print(f"do NOT contact me with unsolicited services or offers {url}")
    else:
        print(f"Unknown {url}")
    sent.append(url)
    with open("sent.txt", "a") as s:
        s.write(f"{url}\n")


def logo():
    print(r"""
    _________               .__             .____    .__          __   
    \_   ___ \____________  |__| ____  _____|    |   |__| _______/  |_ 
    /    \  \/\_  __ \__  \ |  |/ ___\/  ___/    |   |  |/  ___/\   __\
    \     \____|  | \// __ \|  / /_/  >___ \|    |___|  |\___ \  |  |  
     \______  /|__|  (____  /__\___  /____  >_______ \__/____  > |__|  
            \/            \/  /_____/     \/        \/       \/        
=============================================================================
                    CraigsList scraper by @Unix Commerce
=============================================================================
[+] Without browser
[+] Send email alert
[+] Text file input 
_____________________________________________________________________________
""")


def getSoup(url):
    return BeautifulSoup(getRequest(url).text, 'html.parser')


def getJson(params):
    print(f"Getting json from {params}")
    return getRequest(api, params).json()


def getProxy():
    proxy = {}
    if len(proxies) > 0:
        p = random.choice(proxies)
        temp = p.split(":")
        proxy = {
            "http": f"http://{temp[2]}:{temp[3]}@{temp[0]}:{temp[1]}",
            "https": f"http://{temp[2]}:{temp[3]}@{temp[0]}:{temp[1]}"
        }

        print(f"Using proxy {p}.")
    return proxy


def getRequest(url, params=None):
    headers = {'user-agent': 'Opera/9.80 (iPhone; Opera Mini/8.0.0/34.2336; U; en) Presto/2.8.119 Version/11.10'}
    res = requests.get(url, headers=headers, proxies=getProxy(), params=params)
    while "Your request has been blocked." in res.text:
        print("Your request has been blocked. Retrying...")
        time.sleep(random.randint(sleep_time_min, sleep_time_max))
        res = requests.get(url, headers=headers, proxies=getProxy(), params=params)
    return res


categories = {"23": "acc", "35": "act", "106": "aos", "1": "apa", "149": "app", "170": "ard", "135": "art",
              "169": "atd", "150": "atq", "70": "ats", "209": "avd", "208": "avo", "107": "bab", "171": "bad",
              "42": "bar", "198": "bdp", "174": "bfd", "134": "bfs", "172": "bid", "68": "bik", "4": "biz",
              "173": "bkd", "92": "bks", "119": "boa", "164": "bod", "197": "bop", "202": "bpd", "201": "bpo",
              "138": "bts", "12": "bus", "177": "cbd", "176": "cld", "94": "clo", "38": "cls", "95": "clt",
              "207": "cms", "3": "com", "110": "cpg", "76": "cps", "114": "crg", "77": "crs", "100": "csr",
              "146": "ctd", "145": "cto", "109": "cwg", "158": "cys", "113": "dmg", "57": "edu", "48": "egr",
              "167": "eld", "96": "ele", "117": "emd", "175": "emq", "15": "etc", "8": "eve", "115": "evg", "79": "evs",
              "129": "fbh", "154": "fgs", "104": "fns", "179": "fod", "5": "for", "142": "fud", "141": "fuo",
              "73": "gms", "61": "gov", "133": "grd", "91": "grp", "178": "grq", "152": "hab", "180": "had",
              "26": "hea", "2": "hou", "181": "hsd", "97": "hsh", "80": "hss", "54": "hum", "194": "hvd", "193": "hvo",
              "210": "hws", "182": "jwd", "120": "jwl", "56": "kid", "130": "lab", "88": "laf", "111": "lbg",
              "82": "lbs", "47": "lgl", "103": "lgs", "81": "lss", "183": "mad", "13": "mar", "156": "mas",
              "136": "mat", "160": "mcd", "69": "mcy", "25": "med", "63": "mis", "128": "mnu", "153": "mob",
              "165": "mod", "196": "mpd", "195": "mpo", "184": "msd", "98": "msg", "71": "muc", "28": "npo",
              "24": "ofc", "40": "off", "155": "pas", "37": "pet", "185": "phd", "137": "pho", "87": "pol",
              "162": "ppd", "41": "prk", "163": "ptd", "122": "pts", "144": "reb", "127": "rej", "143": "reo",
              "10": "res", "27": "ret", "121": "rew", "36": "rid", "90": "rnr", "18": "roo", "105": "rts", "168": "rvd",
              "124": "rvs", "50": "sad", "58": "sbw", "75": "sci", "200": "sdp", "131": "sec", "186": "sgd",
              "19": "sha", "83": "sks", "49": "sls", "192": "snd", "191": "snw", "21": "sof", "199": "sop",
              "126": "spa", "93": "spo", "39": "sub", "65": "swp", "166": "syd", "7": "sys", "188": "tad", "132": "tag",
              "55": "tch", "52": "tfr", "161": "tid", "44": "tix", "187": "tld", "108": "tlg", "118": "tls",
              "206": "trb", "59": "trd", "205": "tro", "125": "trp", "140": "trv", "99": "vac", "189": "vgd",
              "151": "vgm", "116": "vnn", "29": "vol", "190": "wad", "20": "wan", "11": "web", "139": "wet",
              "112": "wrg", "16": "wri", "204": "wtd", "203": "wto", "101": "zip", "-1": "hsw"}
state_area_id = {"sfbay": 1, "seattle": 2, "newyork": 3, "boston": 4, "losangeles": 7, "sandiego": 8, "portland": 9,
                 "washingtondc": 10, "chicago": 11, "sacramento": 12, "denver": 13, "atlanta": 14, "austin": 15,
                 "philadelphia": 17, "phoenix": 18, "minneapolis": 19, "miami": 20, "dallas": 21, "detroit": 22,
                 "houston": 23, "lasvegas": 26, "cleveland": 27, "honolulu": 28, "stlouis": 29, "kansascity": 30,
                 "neworleans": 31, "nashville": 32, "pittsburgh": 33, "baltimore": 34, "cincinnati": 35, "raleigh": 36,
                 "tampa": 37, "providence": 38, "orlando": 39, "buffalo": 40, "charlotte": 41, "columbus": 42,
                 "fresno": 43, "hartford": 44, "indianapolis": 45, "memphis": 46, "milwaukee": 47, "norfolk": 48,
                 "albuquerque": 50, "anchorage": 51, "boise": 52, "sanantonio": 53, "oklahomacity": 54, "omaha": 55,
                 "saltlakecity": 56, "tucson": 57, "louisville": 58, "albany": 59, "richmond": 60, "greensboro": 61,
                 "santabarbara": 62, "bakersfield": 63, "tulsa": 70, "jacksonville": 80, "reno": 92, "vermont": 93,
                 "eugene": 94, "spokane": 95, "modesto": 96, "stockton": 97, "desmoines": 98, "wichita": 99,
                 "littlerock": 100, "columbia": 101, "monterey": 102, "orangecounty": 103, "inlandempire": 104,
                 "fortmyers": 125, "rochester": 126, "bham": 127, "charleston": 128, "grandrapids": 129,
                 "syracuse": 130, "dayton": 131, "elpaso": 132, "lexington": 133, "jackson": 134, "madison": 165,
                 "harrisburg": 166, "allentown": 167, "newhaven": 168, "maine": 169, "newjersey": 170, "asheville": 171,
                 "annarbor": 172, "westernmass": 173, "puertorico": 180, "tallahassee": 186, "chico": 187,
                 "redding": 188, "humboldt": 189, "chambana": 190, "slo": 191, "montana": 192, "delaware": 193,
                 "wv": 194, "sd": 195, "nd": 196, "wyoming": 197, "nh": 198, "batonrouge": 199, "mobile": 200,
                 "ithaca": 201, "knoxville": 202, "pensacola": 203, "toledo": 204, "savannah": 205, "shreveport": 206,
                 "montgomery": 207, "ventura": 208, "palmsprings": 209, "cosprings": 210, "lansing": 212,
                 "medford": 216, "bellingham": 217, "santafe": 218, "gainesville": 219, "chattanooga": 220,
                 "springfield": 221, "columbiamo": 222, "rockford": 223, "peoria": 224, "springfieldil": 225,
                 "fortwayne": 226, "evansville": 227, "southbend": 228, "bloomington": 229, "gulfport": 230,
                 "huntsville": 231, "salem": 232, "bend": 233, "sarasota": 237, "daytona": 238, "capecod": 239,
                 "worcester": 240, "eauclaire": 242, "appleton": 243, "flagstaff": 244, "micronesia": 245,
                 "yakima": 246, "utica": 247, "binghamton": 248, "hudsonvalley": 249, "longisland": 250,
                 "akroncanton": 251, "youngstown": 252, "greenville": 253, "myrtlebeach": 254, "duluth": 255,
                 "augusta": 256, "macon": 257, "athensga": 258, "flint": 259, "saginaw": 260, "kalamazoo": 261,
                 "up": 262, "mcallen": 263, "beaumont": 264, "corpuschristi": 265, "brownsville": 266, "lubbock": 267,
                 "odessa": 268, "amarillo": 269, "waco": 270, "laredo": 271, "winstonsalem": 272, "fayetteville": 273,
                 "wilmington": 274, "erie": 275, "scranton": 276, "pennstate": 277, "reading": 278, "lancaster": 279,
                 "topeka": 280, "newlondon": 281, "lincoln": 282, "lafayette": 283, "lakecharles": 284, "merced": 285,
                 "southjersey": 286, "fortcollins": 287, "rockies": 288, "roanoke": 289, "charlottesville": 290,
                 "blacksburg": 291, "provo": 292, "fayar": 293, "quadcities": 307, "easttexas": 308, "nmi": 309,
                 "pueblo": 315, "rmn": 316, "boulder": 319, "westslope": 320, "oregoncoast": 321, "eastoregon": 322,
                 "tricities": 323, "kpr": 324, "wenatchee": 325, "collegestation": 326, "killeen": 327,
                 "easternshore": 328, "westmd": 329, "keys": 330, "spacecoast": 331, "treasure": 332, "ocala": 333,
                 "lascruces": 334, "eastnc": 335, "outerbanks": 336, "watertown": 337, "plattsburgh": 338,
                 "iowacity": 339, "cedarrapids": 340, "siouxcity": 341, "bgky": 342, "columbusga": 343, "bn": 344,
                 "carbondale": 345, "visalia": 346, "lawrence": 347, "terrehaute": 348, "cnj": 349, "corvallis": 350,
                 "ogden": 351, "stgeorge": 352, "hiltonhead": 353, "nwct": 354, "altoona": 355, "poconos": 356,
                 "york": 357, "fortsmith": 358, "texarkana": 359, "tippecanoe": 360, "muncie": 361, "dubuque": 362,
                 "lacrosse": 363, "abilene": 364, "wichitafalls": 365, "lynchburg": 366, "danville": 367,
                 "pullman": 368, "stcloud": 369, "yuma": 370, "tuscaloosa": 371, "auburn": 372, "goldcountry": 373,
                 "hattiesburg": 374, "northmiss": 375, "lakeland": 376, "westky": 377, "southcoast": 378,
                 "prescott": 419, "roswell": 420, "mankato": 421, "lawton": 422, "joplin": 423, "eastidaho": 424,
                 "jonesboro": 425, "jxn": 426, "valdosta": 427, "ksu": 428, "grandisland": 432, "stillwater": 433,
                 "centralmich": 434, "fargo": 435, "mansfield": 436, "limaohio": 437, "athensohio": 438,
                 "charlestonwv": 439, "morgantown": 440, "parkersburg": 441, "huntington": 442, "wheeling": 443,
                 "martinsburg": 444, "ames": 445, "boone": 446, "harrisonburg": 447, "logan": 448, "sanmarcos": 449,
                 "catskills": 451, "chautauqua": 452, "elmira": 453, "mendocino": 454, "imperial": 455,
                 "yubasutter": 456, "fredericksburg": 457, "wausau": 458, "roseburg": 459, "annapolis": 460,
                 "skagit": 461, "hickory": 462, "williamsport": 463, "florencesc": 464, "clarksville": 465,
                 "olympic": 466, "dothan": 467, "sierravista": 468, "twinfalls": 469, "galveston": 470, "racine": 552,
                 "janesville": 553, "muskegon": 554, "porthuron": 555, "smd": 556, "staugustine": 557, "jacksontn": 558,
                 "gadsden": 559, "shoals": 560, "jerseyshore": 561, "panamacity": 562, "monroe": 563, "victoriatx": 564,
                 "mohave": 565, "semo": 566, "waterloo": 567, "farmington": 568, "decatur": 569, "brunswick": 570,
                 "sheboygan": 571, "swmi": 572, "sandusky": 573, "virgin": 616, "thumb": 627, "battlecreek": 628,
                 "monroemi": 629, "holland": 630, "northernwi": 631, "swv": 632, "frederick": 633, "onslow": 634,
                 "statesboro": 635, "nwga": 636, "albanyga": 637, "lakecity": 638, "cfl": 639, "okaloosa": 640,
                 "meridian": 641, "natchez": 642, "houma": 643, "cenla": 644, "nacogdoches": 645, "sanangelo": 646,
                 "delrio": 647, "bigbend": 648, "texoma": 649, "enid": 650, "showlow": 651, "elko": 652, "clovis": 653,
                 "lewiston": 654, "moseslake": 655, "missoula": 656, "billings": 657, "bozeman": 658, "helena": 659,
                 "greatfalls": 660, "butte": 661, "kalispell": 662, "bemidji": 663, "brainerd": 664, "marshall": 665,
                 "bismarck": 666, "grandforks": 667, "northplatte": 668, "scottsbluff": 669, "cookeville": 670,
                 "richmondin": 671, "kokomo": 672, "owensboro": 673, "eastky": 674, "klamath": 675, "juneau": 676,
                 "fairbanks": 677, "kenai": 678, "siouxfalls": 679, "rapidcity": 680, "csd": 681, "nesd": 682,
                 "potsdam": 683, "oneonta": 684, "fingerlakes": 685, "glensfalls": 686, "swks": 687, "nwks": 688,
                 "seks": 689, "salina": 690, "ottumwa": 691, "masoncity": 692, "fortdodge": 693, "stjoseph": 694,
                 "loz": 695, "kirksville": 696, "quincy": 697, "lasalle": 698, "mattoon": 699, "ashtabula": 700,
                 "chillicothe": 701, "zanesville": 702, "tuscarawas": 703, "twintiers": 704, "chambersburg": 705,
                 "meadville": 706, "susanville": 707, "siskiyou": 708, "hanford": 709, "santamaria": 710,
                 "winchester": 711, "swva": 712, "eastco": 713}


def checkApi():
    params = (
        ('batch', '45-0-360-0-0'),
        ('cc', 'US'),
        ('lang', 'en'),
        ('searchPath', 'bbb'),
    )
    response = getJson(params)
    print(response)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-smin", "--sleepmin", help="Min sleep time in seconds", type=int, default=5)
    arg_parser.add_argument("-smax", "--sleepmax", help="Max sleep time in seconds", type=int, default=10)
    sleep_time_min = arg_parser.parse_args().sleepmin
    sleep_time_max = arg_parser.parse_args().sleepmax
    main()
