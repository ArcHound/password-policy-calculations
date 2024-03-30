from requests_cache import CachedSession
import logging
from collections import defaultdict
from datetime import timedelta
from bs4 import BeautifulSoup

log = logging.getLogger("pwpolicylogger")


class GCPScraper:
    def __init__(
        self,
        proxy,
        proxies,
        cards,
        base_doc_url="https://cloud.google.com",
        base_api_url="https://prices.gcp.com",
        cache_name="gcp_cache",
        backend="sqlite",
    ):
        log.info("Init gcp session...")
        self.base_url = base_doc_url
        self.api_url = base_api_url
        self.cards = cards
        self.gcp_session = CachedSession(
            cache_name=cache_name,
            backend=backend,
            cache_control=True,
            expire_after=timedelta(days=1),
        )
        self.gcp_api_session = CachedSession(
            cache_name=cache_name + "_api",
            backend=backend,
            cache_control=False,
            expire_after=timedelta(days=1),
        )
        # gcp_session.headers.update({"Authorization": "Bearer {}".format(gcp_token)})
        if proxy:
            log.info("Got proxy {} for gcp".format(proxies))
            self.gcp_session.proxies.update(proxies)
            self.gcp_session.verify = False

    def crawl(self):
        log.info("Crawling gcp")
        path = "/en-us/gcp/virtual-machines/"
        list_r = self.gcp_session.get(self.base_url + path + "sizes-gpu")
        text = BeautifulSoup(list_r.text, "html.parser")
        content = text.find("main")
        ul = content.find_all("ul")[1]
        links = [path + link["href"] for link in ul.find_all("a")]
        self.pricing_reqs = list()
        for link in links:
            try:
                log.debug(link)
                stats = self.parse_vm_details(link)
                self.pricing_reqs += stats
            except Exception as e:
                log.error(f"Bad scrape of {link} - {e}")
        full_data = list()
        for x in self.pricing_reqs:
            try:
                sku = x["sku"]
                prices = self.gcp_api_session.get(
                    self.api_url + "/api/retail/prices",
                    params={
                        "$filter": f"armSkuName eq '{sku}' and priceType eq 'Consumption'"
                    },
                ).json()
                offer = self.parse_pricing(prices)
                x["price"] = offer["unitPrice"]
                x["unit"] = offer["unitOfMeasure"]
                full_data.append(x)
            except Exception as e:
                log.error(f"Cannot get pricing for {x} - {e}")

        # normalize price per 1 GPU
        for x in full_data:
            x["gpu_num"] = float(x["gpu_num"].split(" ")[0])
            x["price"] = x["price"] / x["gpu_num"]

        return full_data

    def parse_vm_details(self, link):
        text_r = self.gcp_session.get(self.base_url + link)
        text = BeautifulSoup(text_r.text, "html.parser")
        content = text.find("main")
        header = [x.string for x in content.find("table").find("thead").find_all("th")]
        row_index = header.index("GPU")
        table = content.find("table").find("tbody")
        gpu_type = ""
        for card in self.cards:
            if card in text_r.text:
                log.debug(card)
                gpu_type = card
        if gpu_type == "":
            raise ValueError("Missing GPU Data, skipping.")
        stats = list()
        for tr in table.find_all("tr"):
            row = [td.string for td in tr.find_all("td")]
            gpu_num = row[row_index]
            if "/" in gpu_num:
                num, den = gpu_num.split("/")
                gpu_num = str(float(num) / float(den))  # ugh. Don't ask
            stats.append({"sku": row[0], "gpu_num": gpu_num, "gpu_type": gpu_type})
        return stats

    def parse_pricing(self, pricing_data):
        less_data = [
            x for x in pricing_data["Items"] if "effectiveEndDate" not in x
        ]  # exclude old offers
        return min(
            less_data, key=lambda x: x["unitPrice"]
        )  # hopefully they're all billed by the hour