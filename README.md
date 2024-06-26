# Password Policy Attacking Costs

Supporting scripts for the article at https://miloslavhomer.cz/password-policy-attacking-costs.
TL:DR; how much do you need to pay Azure for GPU VMs to crack some hashes?

## Data

In the data folder, you can find CSVs with various data related to computing the costs:

 - Azure pricing
 - known GPU hashcat benchmarks
 - map of hashcat modes

## Experiment

I've tested the hypotesis, in the experiment folder there's terraform code to deploy the cracking runner VM.
You'd need a working instance of `az` CLI tool that's authorized with your Azure credentials.
Also, prepare to pay a lot of cash for the VMs. 
You have been warned and I take zero responsibility for your cloud bill.

## Scripts

The scripts contain a lot of scraping and parsing, not that interesting, but useful. 
Create a new virtual env (`python3 venv venv`), activate (`source venv/bin/activate`), install requirements (`pip3 install -r requirements.txt`).

Subcommands:

```
Usage: pw_policy_cost_tool.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  calc            Compute the stats for selected pw policy and sku
  gen-experiment  Generate files for running the cracking experiment
  get-benchmarks  Get benchmark data from onlinehashcrack and Chick3nman...
  get-cloud-data  Get cloud pricing data (azure only)
  stats           Compute the stats (as seen in the article)

```

You should run all the `get-` subcommands first. 
Then probably the most useful is the `calc` subcommand:

```
Usage: pw_policy_cost_tool.py calc [OPTIONS]

  Compute the stats for selected pw policy and sku

Options:
  --benchmark-input-file FILE     Benchmark data input file
  --azure-input-file FILE         Output file
  --hashmode-input-file FILE      CSV with hashcat hashmodes map
  --pw-len INTEGER                Length of the password
  --mode INTEGER                  Hash mode of the hash (refer to modes.csv)
  --sku TEXT                      Specific VM configuration to use (Azure
                                  SKUs) - if set to cheapest, it'd calculate
                                  the cheapest version
  --charset-length INTEGER        Length of character set.
  --log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                                  Set logging level.  [default: WARNING]
  --help                          Show this message and exit.
```
