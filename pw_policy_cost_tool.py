#!/usr/bin/env python3

import os
import json
import csv
import logging
import sys
import time
import math
import warnings
from functools import update_wrapper
from benchmarks.benchmarks import OHCScraper, GistScraper, consolidate_stats
from cloud.azure import AzureScraper
from utils import normalize_device, cards_list, charset_lenghts, calculate_policy_size
import cProfile
import pandas as pd
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


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--benchmark-output-file",
    help="Output file",
    type=click.Path(readable=True, file_okay=True, dir_okay=False),
    default="./data/benchmark.csv",
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
def get_benchmarks(benchmark_output_file, proxy, proxy_address, log_level):
    """Get benchmark data from onlinehashcrack and Chick3nman gists"""
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

    # new_stats = consolidate_stats([data_ohc, data_gists])
    # log.info(json.dumps(new_stats, indent=2))

    return 0


@cli.command()
@click.option(
    "--azure-output-file",
    help="Azure data output file",
    type=click.Path(readable=True, file_okay=True, dir_okay=False),
    default="./data/azure.csv",
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
def get_cloud_data(azure_output_file, proxy, proxy_address, log_level):
    """Get cloud pricing data"""
    # ======================================================================
    #                        Your script starts here!
    # ======================================================================
    proxies = {"http": proxy_address, "https": proxy_address}

    azure = AzureScraper(proxy, proxies, cards_list)
    azure_data = azure.crawl()
    with click.open_file(azure_output_file, "w") as f:
        headers = ["sku", "device", "price", "time unit"]
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in azure_data:
            writer.writerow([row["sku"], row["gpu_type"], row["price"], row["unit"]])
    return 0


@cli.command()
@click.option(
    "--benchmark-input-file",
    help="Benchmark data input file",
    type=click.Path(readable=True, file_okay=True, dir_okay=False),
    default="./data/benchmark.csv",
)
@click.option(
    "--azure-input-file",
    help="Output file",
    type=click.Path(readable=True, file_okay=True, dir_okay=False),
    default="./data/azure.csv",
)
@click.option(
    "--pw-len",
    help="Length of the password",
    type=int,
    default=8,
)
@click.option(
    "--mode",
    help="Hash mode of the hash (refer to modes.csv)",
    type=int,
    default=0,
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
def calc(benchmark_input_file, azure_input_file, pw_len, mode, log_level):
    """Compute the stats"""
    # ======================================================================
    #                        Your script starts here!
    # ======================================================================
    benchmark = pd.read_csv(benchmark_input_file)
    benchmark["device"] = benchmark["device"].apply(normalize_device)
    # log.debug(benchmark)
    azure_data = pd.read_csv(azure_input_file)
    # log.debug(azure_data)
    merged = pd.merge(benchmark, azure_data, how="right", on=["device"])
    # log.debug(merged)

    policy_size = calculate_policy_size(charset_lenghts["ascii_printable"], pw_len)
    log.info(f"Working with policy size {policy_size}")

    relevant_hashes = merged.loc[merged["hashmode"] == mode]
    # log.debug(relevant_hashes)
    with warnings.catch_warnings():
        warnings.simplefilter(action="ignore")
        relevant_hashes["policy_cost"] = (
            policy_size / relevant_hashes["speed"] / 3600 * relevant_hashes["price"]
        )
    # log.debug(relevant_hashes)
    index = relevant_hashes["policy_cost"].idxmin()
    row = relevant_hashes.loc[index]
    click.echo(
        "The cheapest option is {} with GPU {} - total cost {}$".format(
            row["sku"], row["device"], round(row["policy_cost"], 3)
        )
    )
    return 0


@cli.command()
@click.option(
    "--benchmark-input-file",
    help="Benchmark data input file",
    type=click.Path(readable=True, file_okay=True, dir_okay=False),
    default="./data/benchmark.csv",
)
@click.option(
    "--azure-input-file",
    help="Azure costs input file",
    type=click.Path(readable=True, file_okay=True, dir_okay=False),
    default="./data/azure.csv",
)
@click.option(
    "--hashmode-input-file",
    help="CSV with hashcat hashmodes map",
    type=click.Path(readable=True, file_okay=True, dir_okay=False),
    default="./data/modes.csv",
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
def stats(benchmark_input_file, azure_input_file, hashmode_input_file, log_level):
    """Compute the stats"""
    # ======================================================================
    #                        Your script starts here!
    # ======================================================================
    benchmark = pd.read_csv(benchmark_input_file)
    benchmark["device"] = benchmark["device"].apply(normalize_device)
    # log.debug(benchmark)
    azure_data = pd.read_csv(azure_input_file)
    # log.debug(azure_data)
    merged = pd.merge(benchmark, azure_data, how="right", on=["device"])
    # log.debug(merged)

    hashmode_map = dict()
    with open(hashmode_input_file) as f:
        reader = csv.reader(f, delimiter=";")
        for row in reader:
            hashmode_map[row[0]] = row[1]

    # Different hashes on pw_len 8
    click.echo("Different hashes on password length 8")
    policy_size = calculate_policy_size(charset_lenghts["ascii_printable"], 8)
    hashmodes = [0, 10, 100, 1000, 1400, 3200, 8900]
    mapped = [hashmode_map[str(h)] for h in hashmodes]
    prices = list()

    for h in hashmodes:
        relevant_hashes = merged.loc[merged["hashmode"] == h]
        # log.debug(relevant_hashes)
        with warnings.catch_warnings():
            warnings.simplefilter(action="ignore")
            relevant_hashes["policy_cost"] = (
                policy_size / relevant_hashes["speed"] / 3600 * relevant_hashes["price"]
            )
        # log.debug(relevant_hashes)
        index = relevant_hashes["policy_cost"].idxmin()
        row = relevant_hashes.loc[index]

        prices.append(str(round(row["policy_cost"], 3)) + "$")
    results = pd.DataFrame(
        {"Hashmode": hashmodes, "Hash": mapped, "Cracking price": prices}
    )
    click.echo(results.to_markdown())
    click.echo("")

    # MD5 on password lenghts
    click.echo("MD5 on password lengths from 6")
    pw_lens = range(6, 16)
    prices = list()

    for p in pw_lens:
        policy_size = calculate_policy_size(charset_lenghts["ascii_printable"], p)
        relevant_hashes = merged.loc[merged["hashmode"] == 0]
        # log.debug(relevant_hashes)
        with warnings.catch_warnings():
            warnings.simplefilter(action="ignore")
            relevant_hashes["policy_cost"] = (
                policy_size / relevant_hashes["speed"] / 3600 * relevant_hashes["price"]
            )
        # log.debug(relevant_hashes)
        index = relevant_hashes["policy_cost"].idxmin()
        row = relevant_hashes.loc[index]

        prices.append(str(round(row["policy_cost"], 3)) + "$")
    results = pd.DataFrame({"Password length": pw_lens, "Cracking price": prices})
    click.echo(results.to_markdown())
    click.echo("")

    # charsets on MD5 len 12
    click.echo("Different charsets on MD5, password length 12")
    charsets = list(charset_lenghts.keys())
    cs_lens = [charset_lenghts[x] for x in charsets]
    prices = list()

    for c in cs_lens:
        policy_size = calculate_policy_size(c, 12)
        relevant_hashes = merged.loc[merged["hashmode"] == 0]
        # log.debug(relevant_hashes)
        with warnings.catch_warnings():
            warnings.simplefilter(action="ignore")
            relevant_hashes["policy_cost"] = (
                policy_size / relevant_hashes["speed"] / 3600 * relevant_hashes["price"]
            )
        # log.debug(relevant_hashes)
        index = relevant_hashes["policy_cost"].idxmin()
        row = relevant_hashes.loc[index]

        prices.append(str(round(row["policy_cost"], 3)) + "$")
    results = pd.DataFrame(
        {"Charset": charsets, "Charset lenght": cs_lens, "Cracking price": prices}
    )
    click.echo(results.to_markdown())
    click.echo("")
    return 0


if __name__ == "__main__":
    cli(obj={})
