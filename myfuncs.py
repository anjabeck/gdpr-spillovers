from linearmodels import PanelOLS
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import hist
import scipy.stats as stats
import mplhep
mplhep.style.use("LHCb2")


labels = {
    (1, 1): "EU audience\nEU location",
    (0, 1): "non-EU audience\nEU location",
    (1, 0): "EU audience\nnon-EU location",
    (0, 0): "non-EU audience\nnon-EU location",
}
colors = {
    (1, 1): 'firebrick',
    (0, 1): 'dodgerblue',
    (1, 0): 'goldenrod',
    (0, 0): 'darkgreen',
}


def get_trend(dataset, keydate=pd.Timestamp("2018-05-25")):
    trend = (dataset['date'] - dataset['date'].min()).dt.days
    shift = (keydate - dataset['date'].min()).days
    # Drop the centering used for the paper (-6 and +15)
    trend_after = trend - shift  # - 6
    # trend += 15
    trend /= 100
    trend_after /= 100
    return trend, trend_after


def fit_poly(x, y, order=1, weights=None):
    if weights is None:
        fit = np.polyfit(x, y, order)
    else:
        fit = np.polyfit(x, y, order, w=weights)
    return fit


def do_rdd(data, y, window, order=2, cutoff=pd.Timestamp("2018-05-25"), kernel=None):
    diff = np.asarray((data['date'] - cutoff).dt.days)
    sel_pre = (diff < 0) & (diff >= -window)
    sel_post = (diff > 0) & (diff <= window)
    unique_pre = np.unique(diff[sel_pre])
    unique_post = np.unique(diff[sel_post])
    if len(unique_pre) < order+1 or len(unique_post) < order+1:
        return np.nan
    if kernel is None:
        pre_fit = fit_poly(diff[sel_pre], data[sel_pre][y], order=order)
        post_fit = fit_poly(diff[sel_post], data[sel_post][y], order=order)
    else:
        pre_weights = kernel(diff[sel_pre])
        post_weights = kernel(diff[sel_post])
        pre_fit = fit_poly(diff[sel_pre], data[sel_pre][y], order=order,
                           weights=pre_weights)
        post_fit = fit_poly(diff[sel_post], data[sel_post][y], order=order,
                            weights=post_weights)
    value_pre_drop = np.exp(pre_fit[-1]) - 1
    value_post_drop = np.exp(post_fit[-1]) - 1
    drop = (value_post_drop-value_pre_drop)/value_pre_drop
    return drop


def do_adhoc(grouped, cutoff=pd.Timestamp("2018-05-25")):
    sel_pre = grouped.index < cutoff
    if np.sum(sel_pre) == 0 or np.sum(~sel_pre) == 0:
        return np.nan
    else:
        val_pre = grouped[sel_pre].values[-1]
        val_post = grouped[~sel_pre].values[0]
        pre = np.exp(val_pre)-1
        post = np.exp(val_post)-1
        return (post-pre)/pre


def do_regression_allatonce(dataset, ylabel, keydate=pd.Timestamp("2018-05-25"), printoutput=True):
    dataset['after'] = (dataset["date"] >= keydate).astype(int)
    trend, trend_after = get_trend(dataset, keydate=keydate)
    dataset['trend'] = trend
    dataset['trend_after'] = trend_after
    dataset = dataset.set_index(['h', 'date'])

    beta = "trend:C(square)"
    gamma = "trend_after:after:C(square)"
    delta = "after:C(square)"
    formula = f"{ylabel} ~ {beta} + {gamma} + {delta}"

    model = PanelOLS.from_formula(
        formula + " + EntityEffects",
        data=dataset
    )
    res = model.fit(cluster_entity=True, cov_type='clustered')
    if printoutput:
        for i in range(4):
            var = f"{delta}[{i+1}]"
            print(f"\t{var}:\t{res.params[var]:.4f} +/- {res.std_errors[var]:.4f} (p={res.pvalues[var]:.4f})")
    return res.params


def do_regression_twogroups(dataset, measure, eu, ylabel, keydate=pd.Timestamp("2018-05-25"), printoutput=True):
    dataset['after'] = (dataset["date"] >= keydate).astype(int)
    trend, trend_after = get_trend(dataset, keydate=keydate)
    dataset['trend'] = trend
    dataset['trend_after'] = trend_after
    dataset = dataset.set_index(['h', 'date'])

    beta1 = f"trend:eu_{measure}"
    beta2 = f"trend:noneu_{measure}"
    gamma1 = f"trend_after:after:eu_{measure}"
    gamma2 = f"trend_after:after:noneu_{measure}"
    delta1 = f"after:eu_{measure}"
    delta2 = f"after:noneu_{measure}"
    formula = f"{ylabel} ~ {beta1} + {beta2} + {gamma1} + {gamma2} + {delta1} + {delta2}"
    if measure == 'audience':
        require = "eu_location"
    else:
        require = "eu_audience"
    dataset = dataset.query(f"{require} == {eu}")
    if printoutput:
        print(f"    *** {require} == {eu} => {len(dataset)} observations ***")
    model = PanelOLS.from_formula(
        formula + " + EntityEffects",
        data=dataset
    )
    del dataset
    res = model.fit(cov_type='clustered', cluster_entity=True)
    del model
    if printoutput:
        for var in [delta1, delta2]:
            gap = "\t"
            if len(var) < 24:
                gap += "\t"
            if len(var) < 32:
                gap += "\t"
            print(f"\t{var}:{gap}{res.params[var]:.4f} +/- {res.std_errors[var]:.4f} (p={res.pvalues[var]:.4f})")
    return res.params


def keys(key):
    if key == "after:C(square)[1]":
        return (1, 1)
    elif key == "after:C(square)[2]":
        return (0, 1)
    elif key == "after:C(square)[3]":
        return (1, 0)
    elif key == "after:C(square)[4]":
        return (0, 0)


def plot_placebo(dates, results, output):
    if 'requests' in output:
        mi = -9
        ma = 6
    else:
        mi = -15
        ma = 11
    xmin = dates[0]-pd.Timedelta(days=10)
    xmax = dates[-1]+pd.Timedelta(days=10)
    for var in results.keys():
        plt.plot(dates, np.array(results[var])*100, color=colors[var], marker='.')
    for i, var in enumerate(results.keys()):
        plt.text(x=xmin+0.05*(xmax-xmin), y=(mi + (ma-mi)*0.05 * (i+1)),
                 s=labels[var].replace('\n', ' & '),
                 verticalalignment='bottom', horizontalalignment='left',
                 fontsize=24, color=colors[var])
    plt.axvline(x=pd.Timestamp("2018-05-25"), color='k')
    plt.text(x=pd.Timestamp("2018-05-30"), y=ma-0.035*(ma-mi),
            s="GDPR", verticalalignment='top', horizontalalignment='left', fontsize=28)
    plt.axhline(y=0, color='k')
    if 'requests' in output:
        plt.ylabel("Estimated drop in requests [%]")
    else:
        plt.ylabel("Estimated drop in cookies [%]")
    plt.xlim(xmin, xmax)
    plt.ylim(mi, ma)
    plt.xticks(rotation=90)
    plt.grid()
    plt.savefig(output)
    plt.close()


def plot_trend(variable, data, directory):
    xmin = data['date'].min()-pd.Timedelta(days=10)
    xmax = data['date'].max()+pd.Timedelta(days=10)
    norm_range = [pd.Timestamp("2018-01-01"), pd.Timestamp("2018-05-20")]
    for aud in ['eu', 'noneu']:
        for loc in ['eu', 'noneu']:
            datai = data.query(f"{aud}_audience == 1 and {loc}_location == 1")
            bydate = datai.groupby(['date']).mean()[variable]
            norm = bydate[norm_range[0]:norm_range[1]].mean()
            key = (aud == 'eu', loc == 'eu')
            plt.plot(bydate.index, bydate/norm, label=labels[key],
                     color=colors[key], marker='.')
            align = 'center'
            if variable == 'log_cookies3' and loc == 'eu':
                if aud == 'eu':
                    align = 'top'
                else:
                    align = 'bottom'
            plt.text(x=xmax+pd.Timedelta(days=5), y=bydate.iloc[-1]/norm,
                     s=labels[key], verticalalignment=align, horizontalalignment='left',
                     fontsize=24, color=colors[key], linespacing=0.8)
    plt.axvline(x=pd.Timestamp("2018-05-25"), color='k')
    plt.xlim(xmin, xmax)
    ylim = plt.ylim()
    dist = ylim[1]-ylim[0]
    plt.ylim(ylim[0]-0.05*dist, ylim[1]+0.05*dist)
    ylim = plt.ylim()
    plt.fill_betweenx(y=ylim, x1=norm_range[0]-pd.Timedelta(days=7), x2=norm_range[1]+pd.Timedelta(days=7), color='k', alpha=0.1, zorder=-10)
    norm_diff = (norm_range[1]-norm_range[0]).days
    norm_mean = norm_range[0] + pd.Timedelta(days=norm_diff/2)
    plt.text(x=norm_mean, y=ylim[0]+0.03*(ylim[1]-ylim[0]),
             s="Normalization\nrange", verticalalignment='bottom', horizontalalignment='center',
             fontsize=28, color='gray', zorder=10)
    plt.text(x=pd.Timestamp("2018-05-30"), y=ylim[1]-0.035*(ylim[1]-ylim[0]),
             s="GDPR", verticalalignment='top', horizontalalignment='left', fontsize=28)
    plt.xticks(rotation=90)
    plt.grid()
    if variable == 'log_requests3':
        plt.ylabel(r"Normalized $\log(\text{requests}+1)$")
    else:
        plt.ylabel(r"Normalized $\log(\text{cookies}+1)$")
    plt.savefig(f"{directory}/trend.png")
    plt.close()


def check_rdd_window(variable, data, directory, windows, keydate=pd.Timestamp("2018-05-25")):
    for aud in ['eu', 'noneu']:
        for loc in ['eu', 'noneu']:
            datai = data.query(f"{aud}_audience == 1 and {loc}_location == 1")
            drops1 = []
            drops2 = []
            for window in windows:
                drops1.append(do_rdd(datai, variable, window=window, order=1, cutoff=keydate)*100)
                drops2.append(do_rdd(datai, variable, window=window, order=2, cutoff=keydate)*100)
            key = (aud == 'eu', loc == 'eu')
            plt.text(x=windows[-1]+6, y=drops1[4],
                     s=labels[key], verticalalignment='center', horizontalalignment='left',
                     fontsize=24, color=colors[key], linespacing=0.8)
            plt.plot(windows, drops1, color=colors[key], marker='.')
            plt.plot(windows, drops2, color=colors[key], marker='.', alpha=0.5)
    plt.xlabel("Window size [days]")
    if variable == 'log_requests3':
        plt.ylabel("RDD-estimated drop in requests [%]")
    else:
        plt.ylabel("RDD-estimated drop in cookies [%]")
    plt.axvline(x=70, color='k', linestyle=':')
    if variable == 'log_requests3':
        plt.ylim(-8, 0)
    else:
        plt.ylim(-16, -2)
    plt.xlim(windows[0]-5, windows[-1]+5)
    plt.savefig(f"{directory}/RDD_window.png")
    plt.close()


def plot_bootstrapping(results, output):
    if 'requests' in output:
        mi = -9
        ma = 0
    else:
        mi = -15
        ma = -2
    for var in results.keys():
        h = hist.Hist(hist.axis.Regular(100, mi, ma))
        h.fill(np.array(results[var])*100)
        h.view()[h.view() == 0] = np.nan
        mplhep.histplot(h, histtype='fill', color=colors[var], alpha=0.3)
        mplhep.histplot(h, histtype='step', xerr=True, yerr=True, color=colors[var])
    if 'requests' in output:
        plt.xlabel("Estimated drop in requests [%]")
    else:
        plt.xlabel("Estimated drop in cookies [%]")
    ylim = plt.ylim()
    plt.ylim(0, ylim[1]*1.1)
    for i, var in enumerate(list(results.keys())[::-1]):
        std = np.nanstd(results[var])
        plt.text(x=mi+(ma-mi)*0.03, y=ylim[1]*1.05-0.07*ylim[1]*i,
                 s=labels[var].replace('\n', ' & ')+f" (std.$={std*100:.1f}\%$)",
                 verticalalignment='top', horizontalalignment='left',
                 fontsize=24, color=colors[var])
    binwidth = (ma-mi)/70
    plt.ylabel(f"Number of bootstraps /({binwidth:.2f}%)")
    plt.savefig(output)
    plt.close()


def get_pvalues(results):
    pvals_boots = {}
    pvals_sigma = {}
    for var in results.keys():
        pvals_boots[var] = np.sum(np.array(results[var]) > 0)/len(results[var])
        mu = np.nanmean(results[var])
        sigma = np.nanstd(results[var])
        pvals_sigma[var] = stats.norm.sf(np.abs(mu/sigma))
    return {"boots": pvals_boots, "sigma": pvals_sigma}
