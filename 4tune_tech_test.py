# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.14.5
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Teste técnico - Cientista de Dados na 4tune
# ## Bruno Perdigão de Oliveira

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme()

import warnings
warnings.filterwarnings('ignore')

# %%
df = pd.read_csv("data.csv", index_col=0)


# %%
# Create a function to calculate Saver's Match
def calculate_savers_match(initial_age, family_kind, marital_status, accumulated_capital, annual_contribution, income):
    n_years = int(65 - initial_age)
    year = 2020
    match_contrib_max = 0.00
    match_contrib_min = 0.50
    max_match = 10000.00
    additional_savings = 0.00
    inflation = 0.044

    # Assuming that "Husband-Wife" means "married couples filing jointly"
    if family_kind == 1:
        phase_out_min = 41000.00
        phase_out_max = 71000.00
        
    # Assuming that not married "Male-led" or "Female-led" means "married person filing separately", which is equivalent to "single"
    elif (family_kind != 1) & (marital_status == 1):
        phase_out_min = 20500.00
        phase_out_max = 35500.00
        
    # Assuming that all the rest are "head-of-household filers"
    else:
        phase_out_min = 30750.00
        phase_out_max = 53250.00

    for i in range(n_years):
        # Saver's Match is only applied from 2027
        if year >= 2027:
            contribution_amount = income * annual_contribution

            if contribution_amount > max_match:
                contribution_amount = max_match
            
            match_perc = np.interp(income,
                                     [phase_out_min, phase_out_max],
                                     [match_contrib_min, match_contrib_max])

            additional_match = match_perc * contribution_amount

            additional_savings += additional_match

            # Phase-out range will only be adjusted from 2028
            phase_out_min += phase_out_min * inflation
            phase_out_max += phase_out_max * inflation

        year += 1
        income += income * inflation     

    return additional_savings


# %%
# Applying the function into the dataframe
df['additional_retirement_savings'] = df.apply(lambda x: calculate_savers_match(
                                                            x['initial_age'], 
                                                            x['family_kind'], 
                                                            x['marital_status'],
                                                            x['accumulated_capital'], 
                                                            x['annual_contribution'], 
                                                            x['income']), 
                                                            axis=1)

# %%
# Creating a columns with age cohort
bins = [34, 39, 44, 49, 54, 59, 64]
labels = ["34-39","40-44","45-49","50-54","55-59","60-64",]
df["age_cohort"] = pd.cut(df['initial_age'], bins=bins, labels=labels)

# %%
# Creating a columns with new_accumulated_capital
df["new_accumulated_capital"] = df.eval('accumulated_capital + additional_retirement_savings')

# %%
# Calculating Retirement Readness Rating
df.query("new_accumulated_capital >= 0")['weight'].sum()

able_to_afford = df.query("accumulated_capital >= 0")['weight'].sum()
new_able_to_afford = df.query("new_accumulated_capital >= 0")['weight'].sum()
n_people = df['weight'].sum()
rrr = able_to_afford / n_people
new_rrr = new_able_to_afford / n_people
df['rrr'] = rrr
df['new_rrr'] = new_rrr
df

# %%
# Calculating Weighted Average Retirement Savings Shortfall by Race and Age Cohort
deficits_df = df.query("new_accumulated_capital < 0").copy()
deficits_df['total_deficits'] = deficits_df.eval("new_accumulated_capital * weight")
group_df = deficits_df.groupby(['race', 'age_cohort']).sum()
group_df["weighted_rss"] = group_df.eval('total_deficits / weight')
group_df

# %%
# Plot 1

fig, ax = plt.subplots(figsize=(10, 5))

ax.ticklabel_format(style='plain', axis='y')
ax.invert_yaxis()


plot = sns.barplot(group_df.reset_index(), x='race', y='weighted_rss', hue='age_cohort')

plot.set_xlabel("Race")
plot.set_ylabel("Weighted Average Retirement Savings Shortfall")

ylabels = [f"{y/1:.1f}" for y in ax.get_yticks()]
xlabels = {1:"White", 2:"Black", 3:"Hispanic", 4:"Other"}
plot.set_xticklabels(xlabels.values())
plot.set_yticklabels(ylabels)

sns.move_legend(ax, "upper left", bbox_to_anchor=(1, 1))


# %%
# lot 2
df_rrr = df[['rrr', 'new_rrr']] *100


plot = sns.barplot(df_rrr, width=0.4)
ylabels = [f"{y:.0f}%" for y in plot.get_yticks()]
plot.set_yticklabels(ylabels)
xlabels = ["Current", "New"]
plot.set_xticklabels(xlabels)

plot.set_xlabel("Scenario Comparison")
plot.set_ylabel("Retirement Readiness Rating")

for i in plot.containers:
    plot.bar_label(i, fmt="%.2f")



# %%
# Exporting to CSV
final_df = df.drop(['age_cohort', 'additional_retirement_savings', 'rrr', 'new_rrr'], axis=1)
final_df.to_csv("new_scenario.csv")

# %%

# %%
