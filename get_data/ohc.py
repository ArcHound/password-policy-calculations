from requests_cache import CachedSession
import logging
from datetime import timedelta
from bs4 import BeautifulSoup

log = logging.getLogger('pwpolicylogger')

class OHCScraper:
    def __init__(self, base_url, proxy, proxies, cache_name="ohc_cache", backend="sqlite"):
        log.info("Init service onlinehashcrack session...")
        self.base_url = base_url
        self.ohc_session = CachedSession(cache_name=cache_name, backend=backend, cache_control=False, expire_after=timedelta(days=1))
        # ohc_session.headers.update({"Authorization": "Bearer {}".format(ohc_token)})
        if proxy:
            log.info("Got proxy {} for service onlinehashcrack".format(proxies))
            self.ohc_session.proxies.update(proxies)
            self.ohc_session.verify = False

    def crawl(self):
        log.info('Crawling onlinehashcrack')
        list_r = self.ohc_session.get(self.base_url+'/tools-benchmark-hashcat-gtx-1080-ti-1070-ti-rtx-2080-ti-rtx-3090-3080-4090.php')
        text = BeautifulSoup(list_r.text, 'html.parser')
        links = [x['href'] for x in text.find_all('a') if x.string == "Full benchmark here"]
        self.benchmarks = list()
        for link in links:
            try:
                raw_bm = self.scrape_benchmark(link)
            except Exception as e:
                log.error(f'Bad scrape of {link} - {e}')
            self.benchmarks.append(raw_bm)
        full_stats = dict()
        for bm in self.benchmarks:
            dev, stats = self.parse_benchmark(bm)
            full_stats[dev] = stats
        return full_stats

    def scrape_benchmark(self, link):
        text_r = self.ohc_session.get(link)
        text = BeautifulSoup(text_r.text, 'html.parser')
        pre = text.find('div', {"class":"entry-content notopmargin"}).find('pre').string
        return pre
    
    def parse_benchmark(self, benchmark):
        states = ['devices', 'hashmode', 'speed']
        state = 'devices'
        hashmode = ''
        device = ''
        speed = ''
        stats = dict()
        for line in benchmark.splitlines():
            if state == 'devices':
                if line.startswith('* Device #1'):
                    device = line.split(':')[1].split(',')[0].strip()
                    state = 'hashmode'
                    stats = dict()
            elif state == 'hashmode':
                if line.startswith('Hashmode: '):
                    hashmode = line.split(':')[1].split('-')[0].strip()                   
                    state = 'speed'
                elif line.startswith('* Hash-Mode'):
                    hashmode = line.split(' ')[2]
                    state = 'speed'
            elif state == 'speed':
                if line.startswith('Speed.#1'):
                    raw_speed, unit = line.split(':')[1].split('(')[0].strip().split(' ')
                    unit_table = {'H/s':1, 'kH/s':1000, 'MH/s':1000000, 'GH/s':1000000000}
                    speed = float(raw_speed)*unit_table[unit]
                    stats[hashmode] = speed
                    state = 'hashmode'
        return device, stats

