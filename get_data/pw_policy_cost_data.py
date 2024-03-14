#!/usr/bin/env python3

import os
import json
import csv
import logging
import sys
import time
import math
from functools import update_wrapper
from ohc import OHCScraper
import cProfile
import pstats

import click
from dotenv import load_dotenv
import requests
import requests_cache

requests_cache.install_cache(cache_name="pw_policy_cost_data_requests_cache", backend="sqlite", expire_after=10800)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger('pwpolicylogger')


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
        r =  ctx.invoke(f,  *args, **kwargs)
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
            mins = math.floor(t2-t1) // 60
            hours = mins // 60
            secs = (t2-t1) - 60 * mins - 3600 * hours
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
    "--ohc-url",
    type=str,
    envvar="OHC_URL",
    default="https://onlinehashcrack.com",
    help="Base URL for ohc",
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
    envvar="LOG_LEVEL"
)
@log_decorator
@time_decorator
def main(
        benchmark_output_file,
        ohc_url,
        proxy,
        proxy_address,
        log_level):
    """Console script for pw_policy_cost_data."""
    # ======================================================================
    #                        Your script starts here!
    # ======================================================================
    proxies = {"http": proxy_address, "https": proxy_address}

    ohc = OHCScraper(ohc_url, proxy, proxies)
    data = ohc.crawl()

    with click.open_file(benchmark_output_file, "w") as f:
        headers = ["device", "hashmode", "speed"]
        writer = csv.writer(f)
        writer.writerow(headers)
        for dev, value in data.items():
            for hashmode, speed in value.items():
                writer.writerow([dev, hashmode, speed])
    return 0


if __name__ == "__main__":
    main()
