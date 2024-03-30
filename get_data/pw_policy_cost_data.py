#!/usr/bin/env python3

import os
import json
import csv
import logging
import sys
import time
import math
from functools import update_wrapper
from benchmarks import OHCScraper, GistScraper, consolidate_stats
from azure import AzureScraper
from utils import normalize_device, cards_list
import cProfile
import pstats

import click
from dotenv import load_dotenv
import requests
import requests_cache

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("pwpolicylogger")


log_levels = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def log_decorator(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        log.setLevel(log_levels[ctx.params["log_level"]])
        log.info("Starting")
        r = ctx.invoke(f, *args, **kwargs)
        log.info("Finishing")
        return r

    return update_wrapper(new_func, f)


def time_decorator(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        t1 = time.perf_counter()
        try:
            r = ctx.invoke(f, *args, **kwargs)
            return r
        except Exception as e:
            raise e
        finally:
            t2 = time.perf_counter()
            mins = math.floor(t2 - t1) // 60
            hours = mins // 60
            secs = (t2 - t1) - 60 * mins - 3600 * hours
            log.info(f"Execution in {hours:02d}:{mins:02d}:{secs:0.4f}")

    return update_wrapper(new_func, f)


@click.command()
@click.option(
    "--benchmark-output-file",
    help="Output file",
    type=click.Path(readable=True, file_okay=True, dir_okay=False),
    default="../data/benchmark.csv",
)
@click.option(
    "--azure-output-file",
    help="Output file",
    type=click.Path(readable=True, file_okay=True, dir_okay=False),
    default="../data/azure.csv",
)
@click.option(
    "--proxy",
    is_flag=True,
    help="Whether to use the proxy",
    envvar="PROXY",
)
@click.option(
    "--proxy-address",
    default="http://localhost:8080",
    help="Proxy address",
    envvar="PROXY_ADDRESS",
)
@click.option(
    "--log-level",
    default="WARNING",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    show_default=True,
    help="Set logging level.",
    envvar="LOG_LEVEL",
)
@log_decorator
@time_decorator
def main(benchmark_output_file, azure_output_file, proxy, proxy_address, log_level):
    """Console script for pw_policy_cost_data."""
    # ======================================================================
    #                        Your script starts here!
    # ======================================================================
    proxies = {"http": proxy_address, "https": proxy_address}

    ohc = OHCScraper(proxy, proxies)
    gists = GistScraper(proxy, proxies)
    data_ohc = ohc.crawl()
    data_gists = gists.crawl()

    # checkpoint here, we can consolidate devs later
    with click.open_file(benchmark_output_file, "w") as f:
        headers = ["device", "hashmode", "speed"]
        writer = csv.writer(f)
        writer.writerow(headers)
        for bm, d in data_ohc.items():
            for dev, value in d.items():
                for hashmode, speed in value.items():
                    writer.writerow([dev, hashmode, speed])
        for bm, d in data_gists.items():
            for dev, value in d.items():
                for hashmode, speed in value.items():
                    writer.writerow([dev, hashmode, speed])

    new_stats = consolidate_stats([data_ohc, data_gists])
    log.info(json.dumps(new_stats, indent=2))

    # log.info(f"I've got these cards: {cards}")
    azure = AzureScraper(proxy, proxies, cards_list)
    azure_data = azure.crawl()
    with click.open_file(azure_output_file, "w") as f:
        headers = ["sku", "device", "price", "time unit"]
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in azure_data:
            writer.writerow([row["sku"], row["gpu_type"], row["price"], row["unit"]])
    return 0


if __name__ == "__main__":
    main()
