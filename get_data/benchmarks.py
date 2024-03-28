from requests_cache import CachedSession
import logging
from datetime import timedelta
from collections import defaultdict
from bs4 import BeautifulSoup
from utils import normalize_device

log = logging.getLogger("pwpolicylogger")


def consolidate_stats(stat_list):
    total_stats = defaultdict(list)
    for x in stat_list:
        for source in x:
            for dev in x[source]:
                if normalize_device(dev):
                    total_stats[normalize_device(dev)].append(x[source][dev])
    # should be avg here, but can't be bothered rn
    for x in total_stats:
        total_stats[x] = total_stats[x][0]
    return total_stats


def parse_hashcat_benchmark(benchmark):
    no_devices = 16  # Ugly, but should be enough
    errors = [
        "CUDA SDK Toolkit installation NOT detected or incorrectly installed.",
        "WARNING",
    ]
    states = ["devices", "hashmode", "speed"]
    state = "devices"
    hashmode = ""
    devices = dict()
    speeds = dict()
    stats = dict()
    lines = benchmark.splitlines()
    counter = 0
    unit_table = {
        "H/s": 1,
        "kH/s": 1000,
        "MH/s": 1000000,
        "GH/s": 1000000000,
    }
    while counter < len(lines):
        line = lines[counter]
        if state == "devices":
            moved = False
            for i in range(1, no_devices + 1):
                line = lines[counter]
                if line.startswith(f"* Device #{i}") and all(
                    [error not in line for error in errors]
                ):
                    devices[i] = line.split(":")[1].split(",")[0].strip()
                    counter += 1
                    if counter >= len(lines):
                        break
                    moved = True
                else:
                    break
            if moved:
                state = "hashmode"
        elif state == "hashmode":
            if line.startswith("Hashmode: "):
                hashmode = line.split(":")[1].split("-")[0].strip()
                state = "speed"
            elif line.startswith("* Hash-Mode"):
                hashmode = line.split(" ")[2]
                state = "speed"
        elif state == "speed":
            speeds = dict()
            moved = False
            for i in range(1, no_devices + 1):
                line = lines[counter]
                if line.startswith(f"Speed.#{i}") or line.startswith(f"Speed.Dev.#{i}"):
                    raw_speed, unit = (
                        line.split(":")[1].split("(")[0].strip().split(" ")
                    )
                    speeds[i] = float(raw_speed) * unit_table[unit]
                    counter += 1
                    if counter >= len(lines):
                        break
                    moved = True
                else:
                    break
            if moved:
                stats[hashmode] = speeds
                state = "hashmode"
        counter += 1
    more_stats = dict()
    for i in devices:
        more_stats[devices[i] + " #" + str(i)] = {
            hashmode: stats[hashmode][i] for hashmode in stats
        }
    return more_stats


class GistScraper:
    def __init__(
        self,
        proxy,
        proxies,
        base_url="https://api.github.com",
        cache_name="gh_cache",
        backend="sqlite",
    ):
        log.info("Init github gist session...")
        self.base_url = base_url
        self.gist_session = CachedSession(
            cache_name=cache_name,
            backend=backend,
            cache_control=False,
            expire_after=timedelta(days=1),
        )
        if proxy:
            log.info("Got proxy {} for github gist".format(proxies))
            self.gist_session.proxies.update(proxies)
            self.gist_session.verify = False

    def crawl(self, username="Chick3nman"):
        log.info(f"Crawling gists of {username}")
        list_r = self.gist_session.get(
            self.base_url + f"/users/{username}/gists"
        ).json()
        links = [
            gist["files"][f]["raw_url"]
            for gist in list_r
            for f in gist["files"]
            if "benchmark" in gist["description"].lower()
        ]
        self.benchmarks = list()
        for link in links:
            try:
                raw_bm = self.gist_session.get(link).text
            except Exception as e:
                log.error(f"Bad scrape of {link} - {e}")
            self.benchmarks.append(raw_bm)
        full_stats = dict()
        counter = 0
        for bm in self.benchmarks:
            counter += 1
            stats = parse_hashcat_benchmark(bm)
            full_stats[f"gist_bm_{counter}"] = stats
        return full_stats


class OHCScraper:
    def __init__(
        self,
        proxy,
        proxies,
        base_url="https://onlinehashcrack.com",
        cache_name="ohc_cache",
        backend="sqlite",
    ):
        log.info("Init onlinehashcrack session...")
        self.base_url = base_url
        self.ohc_session = CachedSession(
            cache_name=cache_name,
            backend=backend,
            cache_control=False,
            expire_after=timedelta(days=1),
        )
        # ohc_session.headers.update({"Authorization": "Bearer {}".format(ohc_token)})
        if proxy:
            log.info("Got proxy {} for onlinehashcrack".format(proxies))
            self.ohc_session.proxies.update(proxies)
            self.ohc_session.verify = False

    def crawl(self):
        log.info("Crawling onlinehashcrack")
        list_r = self.ohc_session.get(
            self.base_url
            + "/tools-benchmark-hashcat-gtx-1080-ti-1070-ti-rtx-2080-ti-rtx-3090-3080-4090.php"
        )
        text = BeautifulSoup(list_r.text, "html.parser")
        links = [
            x["href"] for x in text.find_all("a") if x.string == "Full benchmark here"
        ]
        self.benchmarks = list()
        for link in links:
            try:
                raw_bm = self.scrape_benchmark(link)
            except Exception as e:
                log.error(f"Bad scrape of {link} - {e}")
            self.benchmarks.append(raw_bm)
        full_stats = dict()
        counter = 0
        for bm in self.benchmarks:
            counter += 1
            stats = parse_hashcat_benchmark(bm)
            full_stats[f"ohc_bm_{counter}"] = stats
        return full_stats

    def scrape_benchmark(self, link):
        text_r = self.ohc_session.get(link)
        text = BeautifulSoup(text_r.text, "html.parser")
        pre = (
            text.find("div", {"class": "entry-content notopmargin"}).find("pre").string
        )
        return pre
