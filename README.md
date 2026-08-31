# Spillover effects of the GDPR
This repository contains a little study based on the publication
>C. Peukert et. al.: _Regulatory Spillovers and Data Governance: Evidence from the GDPR_, MARKETING SCIENCE 41 (4) 2022

It started from the code published [in this accompanying repository](plots_requests/https://github.com/cpeukert/gdpr/tree/main) and uses the data published alongside the paper.

# Table of Contents
1. [Background](#background)
2. [Visualization](#visualization)
3. [Methods](#methods)
4. [Results](#results)
5. [Discussion](#discussion)
6. [Reproducibility](#reproducibility)

## Background
The General Data Protection Regulation (GDPR) is an EU legal framework protecting consumers from excessive data collection. It went into effect on May 25th 2018. It impacts in particular the online space. Importantly, it has global reach as it protects all users located within the EU regardless of a website's location AND applies to all websites within the EU regardless of the user's location. When analysing the impact of the GDPR, there are four distinct categories:
1. <span style="color:firebrick">EU audience and EU location</span>
2. <span style="color:dodgerblue">non-EU audience and EU location</span>
3. <span style="color:goldenrod">EU audience and non-EU location</span>
4. <span style="color:darkgreen">non-EU audience and non-EU location</span>

The GDPR applies directly in categories 1-3. Due to the global nature of the internet and the large economic power of the EU, regulatory spillover effects into <span style="color:darkgreen">category 4</span> are possible and are examined in the following using visualization and three different quantitative methods.

## Visualization
The two figures below show the trends of (left) the logarithm of the number of third-party requests plus 1 and (right) the logarithm of the number of third-party cookies plus 1 from May 2017 to November 2018 for each of the four categories. In order to facilitate the visual comparison, each category is scaled such that the average value from January 2018 to May 2018 equals one. The EU GDPR became effective on the 25th of May 2018, marked using a vertical solid line. A purely visual inspection shows similar trends for the growth in number of third-party requests and cookies for the four categories throughout the considered timespan with a clear interruption around mid 2018. This drop is largest in <span style="color:firebrick">category 1 (EU audience and EU location)</span> and least notable in <span style="color:darkgreen">category 4 (non-EU audience and non-EU location)</span>.

There are two additional interesting features mainly visible for the number of third-party cookies. First, a gradual increase between two more moderate eras during the fall of 2017. This is possibly a reflection of the seasonal release of new tech and a pre-holiday ramp-up in ads which is hard to verify given the data set only includes two fall seasons. Second, a drop in the number of third-party cookies during fall 2018. This coincides with new releases for the Safari and Firefox browsers that introduced much stricter tracking protections compared to their predecessors.
Number of third-party requests | Number of third-party cookies
:---:|:---:
![IMAGE](plots_requests/trend.png) | ![IMAGE](plots_cookies/trend.png)

In the following, I estimate the impact of the GDPR in all four categories quantitatively using three different methods.

## Methods
**Ad-hoc drop estimate**
A very simple way to determine the magnitude of the drop is to simply calculate the relative change between the last point before the event and the first point after the event for each category.

**Regression Discontinuity Design**
Regression discontinuity analysis considers several points in a window before and after the event to estimate the drop. The trend pre and post the event are determined independently through a linear or quadratic fit to the data points within a range right before and after. The change due to the treatment is the difference between the two functions at the treatment date. The size of the window has significant impact on the computed values. The figures below show a scan of different windows for (left) the number of requests and (right) the number of cookies. The bold data points correspond to fitting a linear function while the slightly transparent data points correspond to fitting a quadratic function. Note that the minimum window size is 30 days (40 days) for the linear (quadratic) function because the minimum number of data points to determine all parameters of a linear (quadratic) function is two (three) and the data points only appear on the 1st and 15th of every month.
For some categories, the magnitude of the drop increases with window size. However, it is preferrable to stick to a smaller window to avoid including unrelated events far before or after the treatment. For most variables, the difference between a linear and quadratic function is small. As a consequence, the nominal window size is chosen to be 70, corresponding to at least four data points in each fit.
Number of requests | Number of cookies
:---:|:---:
![IMAGE](plots_requests/RDD_window.png) | ![IMAGE](plots_cookies/RDD_window.png)


**Differences in Differences**
The impact on the EU audience can be estimated by comparing it to the change in requests and cookies for the non-EU audience. And similarly for the EU location. To this end, the trend before and after the GDPR introduction is fitted in both groups simultaneously while accounting for common effects. The tool used for these fits is PanelOLS from the python package linearmodels. As a cross check, this fit is performed comparing the EU audience and non-EU audience groups, the EU location and non-EU location groups, and all four categories at once. The numerical values obtained for the drops are identical between the three tests which indicates that the problem is saturated, i.e. there is enough data to unambiguously determine all parameters. 

## Results
The following figures represent different aspects of the numerical analysis.

**Placebo tests**
A useful test is to check the reliability of results is to calculate the drops for random points in time. Doing this check for the ad-hoc calculation results in values close to zero for most of the range and strongly negative values at the GDPR introduction data as well as less extreme negative values around the introduction of the new browsers. Applying the RDD to random points in time results in zero values for large regions but much higher variations in some places. Distinctly, right around the GDPR introduction date, the values indicate an increase in traffic. The reason for this are dampening effects right before and after. Some websites have likely adjusted their contents ahead of time while others are lagging behind. Fitting only a short range of data points only captures these changes rather than the larger trends. The DiD method which does include the entire range on the other hand does not show zero change but rather a continuous change towards positive values when moving away from the true introduction date. This is a reflection of the overall positive trend in the data.

**Bootstrapping**
A reliable way to determine stability of a method and determine the behaviour of statistical fluctuations is to apply the method on randomly sampled data points. In an ideal world, the distribution of the parameters obtained from the different samples is truly Gaussian. This is roughly true for all methods considered here. The fraction of data points sitting below corresponds to the p-value of the parameter being different from zero.

### Number of third-party requests
Ad-hoc | RDD | DiD
:---:|:---:|:---:
![IMAGE](plots_requests/adhoc_placebo.png) | ![IMAGE](plots_requests/RDD_placebo.png) | ![IMAGE](plots_requests/DiD_placebo.png)
![IMAGE](plots_requests/adhoc_bootstrap.png) | ![IMAGE](plots_requests/RDD_bootstrap.png) | ![IMAGE](plots_requests/DiD_bootstrap.png)

### Number of third-party cookies
Ad-hoc | RDD | DiD
:---:|:---:|:---:
![IMAGE](plots_cookies/adhoc_placebo.png) | ![IMAGE](plots_cookies/RDD_placebo.png) | ![IMAGE](plots_cookies/DiD_placebo.png)
![IMAGE](plots_cookies/adhoc_bootstrap.png) | ![IMAGE](plots_cookies/RDD_bootstrap.png) | ![IMAGE](plots_cookies/DiD_bootstrap.png)


## Discussion
All four categories experience a significant drop in the number of third-party requests and cookies coinciding when the GDPR came into effect. The impact is largest in <span style="color:firebrick">category 1 (EU audience and EU location)</span> and lowest in <span style="color:darkgreen">category 4 (non-EU audience and non-EU location)</span>. The mixed categories <span style="color:goldenrod">2 (EU audience and non-EU location)</span> and <span style="color:dodgerblue">3 (non-EU audience and EU location)</span> are affected by a similar moderate amount. Nevertheless, even the least affected category experiences a statistically significant drop. The $p$-value for the significance of the drop in requests or cookies, using any of the three methods, is $p<0.002$ when estimated using the number of bootstraps resulting in a drop above 0. Note that this number is limited by running only 500 bootstraps. Out of the three methods and two metrics, the largest $p$-value estimated using on the mean and standard deviation and assuming a Gaussian distribution is of order $p\approx \mathcal{O}(10^{-25})$.

The values estimated by the ad-hoc and RDD methods are very similar while the DiD values deviate slightly. When considering the number of requests, the DiD method results more extreme values than the other two methods. This is likely due to including the steeper than average slopes during October 2017 and 2018. When considering the number of third-party cookies, the DiD method estimates values that are less extreme. This might be due to including the second drop in fall 2018 which decreases the overall slope of the trend after the GDPR introduction date. Generously removing the holiday season and only considering data collected between January 2018 and August 2018, including, moves the DiD estimates closer to the other estimates. While the difference is significantly reduced for all cases, it is not always eliminated. A further reduction of the range to the windows used in the RDD estimate (70 days before and after the GDPR effective date), moves the DiD estimates even closer to the other two estimates. The numerical values are shown in the tables below. Interestingly, the DiD estimates in the most narrow window sit mostly either between the ad-hoc and RDD estimates or are less extreme. The DiD method considers all categories at accounting for parallel effects. As a consequence, it is possible that these less extreme values are closer to the truth as the other two methods are blind to such global effects.

These numerical results and checks emphasize the suspicion that EU legislation can have significant impact on individuals outside the immediate jurisdiction. In the case of the GDPR, there are statistically significant and robust spillover effects improving data protection for individuals outside the EU accessing websites located outside the EU.

**Third-party requests**
Category | DiD (full range) | DiD (2018 Jan-Aug) | DiD (GDPR +/-70 days) | Ad-hoc | RDD
:---:|:---:|:---:|:---:|:---:|:---:
<span style="color:firebrick">EU audience and EU location</span> | $-7.9\%$ | $-7.1\%$ | $-6.5\%$ | $-6.9\%$ | $-6.9\%$
<span style="color:dodgerblue">non-EU audience and EU location</span> | $-4.6\%$ | $-3.8\%$ | $-3.0\%$ | $-3.9\%$ | $-3.9\%$
<span style="color:goldenrod">EU audience and non-EU location</span> | $-5.1\%$ | $-3.6\%$ | $-3.6\%$ | $-3.2\%$ | $-3.3\%$
<span style="color:darkgreen">non-EU audience and non-EU location</span> | $-2.2\%$ | $-1.3\%$ | $-1.2\%$ | $-1.3\%$ | $-1.1\%$

**Third-party cookies**
Category | DiD (full range) | DiD (2018 Jan-Aug) | DiD (GDPR +/-70 days) | Ad-hoc | RDD
:---:|:---:|:---:|:---:|:---:|:---:
<span style="color:firebrick">EU audience and EU location</span> | $-13.3\%$ | $-13.6\%$ | $-10.7\%$ | $-11.4\%$ | $-10.8\%$
<span style="color:dodgerblue">non-EU audience and EU location</span> | $-9.4\%$ | $-9.3\%$ | $-6.9\%$ | $-7.7\%$ | $-6.3\%$
<span style="color:goldenrod">EU audience and non-EU location</span> | $-7.6\%$ | $-8.0\%$ | $-6.5\%$ | $-6.9\%$ | $-6.9\%$
<span style="color:darkgreen">non-EU audience and non-EU location</span> | $-4.6\%$ | $-4.4\%$ | $-2.9\%$ | $-4.0\%$ | $-3.6\%$
## Reproducibility
```
conda create -n gdpr314 python=3.14
conda activate gdpr314
pip install -r requirements.txt
python analyse.py requests
python analyse.py cookies
```