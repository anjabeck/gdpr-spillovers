import os
import argparse
import pandas as pd
import tqdm
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import myfuncs as mf
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser(description="Run analysis on GDPR data")
parser.add_argument("yvar", type=str,
                    help="Which yvar to analyze (requests or cookies)",
                    choices=["requests", "cookies"])
args = parser.parse_args()
yvar = f"log_{args.yvar}3"

directory = f"plots_{args.yvar}"

if not os.path.exists(directory):
    os.mkdir(directory)

filedir = "peukert_et_al_gdpr_data_updated"
filepath = os.path.join(filedir, "gdpr_website.dta")

data = pd.read_stata(filepath)

data.query("exclude == 0", inplace=True)

logging.info(f"Data loaded from {filepath}. Shape: {data.shape}")

gdpr_date = pd.Timestamp("2018-05-25")
rdd_windows = range(30, 200, 10)

# colors = {'trend': 'firebrick', 'trend_after': 'dodgerblue'}

# for col in ['trend', 'trend_after']:
#     plt.plot(data['date'], data[col], label=col, rasterized=True, color=colors[col])
# trend, trend_after = mf.get_trend(data, keydate=gdpr_date)
# plt.plot(data['date'], trend, ls=':', label='mytrend', rasterized=True, color=colors['trend'])
# plt.plot(data['date'], trend_after, ls=':', label='mytrend_after', rasterized=True, color=colors['trend_after'])
# plt.axvline(x=gdpr_date, color='k')
# plt.text(x=pd.Timestamp("2018-05-30"), y=-2, s="GDPR", verticalalignment='center', horizontalalignment='left', fontsize=28, rotation=90)
# plt.axhline(y=0, color='k')
# plt.legend(loc='upper left')
# plt.xticks(rotation=90)
# plt.savefig(f"{directory}/trend.png")
# plt.close()

logging.info("Plotting trends")
mf.plot_trend(yvar, data, directory)

logging.info("Checking RDD window sizes")
mf.check_rdd_window(yvar, data, directory, windows=rdd_windows, keydate=gdpr_date)

logging.info("Calculating placebo results for RDD, ad-hoc")
min_keydate = data['date'].min() + pd.Timedelta(days=60)
max_keydate = data['date'].max() - pd.Timedelta(days=60)

results_rdd = {(0, 0): [], (1, 0): [], (0, 1): [], (1, 1): []}
results_adhoc = {(0, 0): [], (1, 0): [], (0, 1): [], (1, 1): []}
results_did = {(0, 0): [], (1, 0): [], (0, 1): [], (1, 1): []}

daily = [keydate for keydate in pd.date_range(start=data['date'].min(), end=data['date'].max(), freq='1D')]
for aud in ['eu', 'noneu']:
    for loc in ['eu', 'noneu']:
        datai = data.query(f"{aud}_audience == 1 and {loc}_location == 1")
        grouped = datai.groupby(['date']).mean()[yvar]
        key = (aud == 'eu', loc == 'eu')
        for t in tqdm.tqdm(range(len(daily)), desc=f"{aud} aud. {loc} loc."):
            if min_keydate <= daily[t] <= max_keydate:
                drop = mf.do_rdd(datai, yvar, window=70, order=1, cutoff=daily[t])
            else:
                drop = np.nan
            results_rdd[key].append(drop)
            results_adhoc[key].append(mf.do_adhoc(grouped, cutoff=daily[t]))

logging.info("Calculating placebo results for DiD")
weeks_below = (gdpr_date - data['date'].min()).days // 14
start = gdpr_date + pd.Timedelta(days=-weeks_below*14)
biweekly = [keydate for keydate in pd.date_range(start=start, end=data['date'].max(), freq='14D')]
for t in tqdm.tqdm(range(len(biweekly)), desc=f"DiD placebo"):
    if min_keydate <= biweekly[t] <= max_keydate:
        res = mf.do_regression_allatonce(data, yvar, keydate=biweekly[t], printoutput=False)
        for var in res.keys():
            if var.startswith("after:C(square)"):
                results_did[mf.keys(var)].append(res[var])
    else:
        for var in results_did.keys():
            results_did[var].append(np.nan)

mf.plot_placebo(daily, results_rdd, f"{directory}/RDD_placebo.png")
mf.plot_placebo(daily, results_adhoc, f"{directory}/adhoc_placebo.png")
mf.plot_placebo(biweekly, results_did, f"{directory}/DiD_placebo.png")


logging.info("Calculating bootstrap results for RDD, ad-hoc")
results_rdd = {(0, 0): [], (1, 0): [], (0, 1): [], (1, 1): []}
results_adhoc = {(0, 0): [], (1, 0): [], (0, 1): [], (1, 1): []}
results_did = {(0, 0): [], (1, 0): [], (0, 1): [], (1, 1): []}
max_workers = 2
max_samples = max_workers
nsamples = 500
seeds = np.random.randint(0, 10000, size=nsamples)

for aud in ['eu', 'noneu']:
    for loc in ['eu', 'noneu']:
        datai = data.query(f"{aud}_audience == 1 and {loc}_location == 1")
        indices = datai.groupby('h').indices
        hvalues = datai['h'].unique()
        key = (aud == 'eu', loc == 'eu')
        for t in tqdm.tqdm(range(nsamples), desc=f"{aud} aud. {loc} loc."):
            hsubsample = np.random.choice(hvalues, size=len(hvalues), replace=True)
            row_positions = np.concatenate([indices[h] for h in hsubsample])
            subsample = datai.iloc[row_positions].copy()
            subsample['h'] = np.repeat(np.arange(len(hsubsample)), [len(indices[h]) for h in hsubsample])
            drop = mf.do_rdd(subsample, yvar, window=70, order=1, cutoff=gdpr_date)
            results_rdd[key].append(drop)
            grouped = subsample.groupby(['date']).mean()[yvar]
            results_adhoc[key].append(mf.do_adhoc(grouped, cutoff=gdpr_date))
mf.plot_bootstrapping(results_rdd, f"{directory}/RDD_bootstrap.png")
mf.plot_bootstrapping(results_adhoc, f"{directory}/adhoc_bootstrap.png")
logging.info("Calculating bootstrap results for DiD")
indices = data.groupby('h').indices
hvalues = data['h'].unique()
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = []
    dates = []
    pending = {}
    t = 0
    with tqdm.tqdm(total=nsamples, desc="DiD bootstrap") as pbar:
        while t < nsamples or pending:
            while t < nsamples and len(pending) < max_samples:
                hsubsample = np.random.choice(hvalues, size=len(hvalues), replace=True)
                row_positions = np.concatenate([indices[h] for h in hsubsample])
                subsample = data.iloc[row_positions].copy()
                subsample['h'] = np.repeat(np.arange(len(hsubsample)), [len(indices[h]) for h in hsubsample])
                fut = executor.submit(mf.do_regression_allatonce, subsample, yvar, keydate=gdpr_date, printoutput=False)
                pending[fut] = None
                futures.append(fut)
                t += 1
            done = next(as_completed(pending))
            res = done.result()
            for var in res.keys():
                if var.startswith("after:C(square)"):
                    results_did[mf.keys(var)].append(res[var])
            futures.append(res)
            del pending[done]
            pbar.update(1)

mf.plot_bootstrapping(results_did, f"{directory}/DiD_bootstrap.png")

pvals_rdd = mf.get_pvalues(results_rdd)
pvals_adhoc = mf.get_pvalues(results_adhoc)
pvals_did = mf.get_pvalues(results_did)

for var in results_rdd.keys():
    logging.info(f"RDD {var}:\tboots={pvals_rdd['boots'][var]:.2e}, sigma={pvals_rdd['sigma'][var]:.2e}")
    logging.info(f"Ad-hoc {var}:\tboots={pvals_adhoc['boots'][var]:.2e}, sigma={pvals_adhoc['sigma'][var]:.2e}")
    logging.info(f"DiD {var}:\tboots={pvals_did['boots'][var]:.2e}, sigma={pvals_did['sigma'][var]:.2e}")


logging.info("Calculating nominal results")

results_rdd = {}
results_adhoc = {}
results_did_nominal = {}
results_did_noholiday = {}
results_did_same_range = {}

for aud in ['eu', 'noneu']:
    for loc in ['eu', 'noneu']:
        datai = data.query(f"{aud}_audience == 1 and {loc}_location == 1")
        grouped = datai.groupby(['date']).mean()[yvar]
        key = (aud == 'eu', loc == 'eu')
        results_rdd[key] = mf.do_rdd(datai, yvar, window=70, order=1, cutoff=gdpr_date)
        results_adhoc[key] = mf.do_adhoc(grouped, cutoff=gdpr_date)

res = mf.do_regression_allatonce(data, yvar, keydate=gdpr_date, printoutput=False)
for var in res.keys():
    if var.startswith("after:C(square)"):
        results_did_nominal[mf.keys(var)] = res[var]

logging.info("Calculating results without seasonal effects")

data = data.query("'2018-01-01' <= date <= '2018-08-31'")

res = mf.do_regression_allatonce(data, yvar, keydate=gdpr_date, printoutput=False)
for var in res.keys():
    if var.startswith("after:C(square)"):
        results_did_noholiday[mf.keys(var)] = res[var]

# Only look at dates +/-70 days around GDPR date
min_keydate = gdpr_date - pd.Timedelta(days=70)
max_keydate = gdpr_date + pd.Timedelta(days=70)
data = data.query("@min_keydate <= date <= @max_keydate")

res = mf.do_regression_allatonce(data, yvar, keydate=gdpr_date, printoutput=False)
for var in res.keys():
    if var.startswith("after:C(square)"):
        results_did_same_range[mf.keys(var)] = res[var]

for var in results_rdd.keys():
    print(f"{mf.labels[var].replace("\n", " & ")} | ${results_did_nominal[var]*100:.1f}\%$ | ${results_did_noholiday[var]*100:.1f}\%$ | ${results_did_same_range[var]*100:.1f}\%$ | ${results_rdd[var]*100:.1f}\%$ | ${results_adhoc[var]*100:.1f}\%$")
