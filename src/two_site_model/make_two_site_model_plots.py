#  Make nice version of the plots for the two site model
from two_site_model import get_f
import matplotlib.pyplot as plt
import pandas as pd
import os
import time
import argparse
import seaborn as sns
import matplotlib.ticker as ticker
import matplotlib.colors as mcolors
import matplotlib as mpl
import numpy as np
from multiprocessing import Pool

mpl.rcParams["figure.dpi"] = 600
mpl.rcParams["font.sans-serif"] = "Arial"
# mpl.rcParams["font.sans-serif"] = "Liberation Sans"

# print(mpl.get_cachedir())

# data_color = sns.color_palette("ch:s=-1.5,r=-0.8,h=0.7,d=0.25,l=0.9,g=1_r",n_colors=5)[0]
irf_color = "#5D9FB5"
nfkb_color = "#BA4961"
data_color = "#6F5987"
# data_color = "#7C5897"

states_cmap_pars = "ch:s=2.2,r=0.75,h=0.6,l=0.8,d=0.25"
# models_cmap_pars = "ch:s=0.9,r=-0.75,h=0.6,l=0.8,d=0.3"
# sns.cubehelix_palette(n_colors=4, start=0.2,gamma=1,rot=0.4,hue=0.8,dark=0.3,light=0.8,reverse=True)
# models_cmap_pars = "ch:s=-1.5,r=-0.8,h=0.7,d=0.25,l=0.9,g=1_r"
# models_cmap_pars = "ch:s=-0.0,r=0.6,h=1,d=0.3,l=0.8,g=1_r"

# data_color = "#FA4B5C"
# data_color = sns.cubehelix_palette(n_colors=5, start=-0.5,rot=0.5,hue=0.7,dark=0.15,light=0.8,reverse=True)[0]
# states_cmap_pars = "ch:s=2.2,r=0.75,h=0.6,l=0.8,d=0.25"
# # models_cmap_pars = "ch:s=0.9,r=-0.75,h=0.6,l=0.8,d=0.3"
# # sns.cubehelix_palette(n_colors=4, start=0.2,gamma=1,rot=0.4,hue=0.8,dark=0.3,light=0.8,reverse=True)
# models_cmap_pars = "ch:s=-0.4,r=0.7,h=0.7,d=0.3,l=0.9,g=1_r"
# heatmap_cmap = sns.cubehelix_palette(as_cmap=True, light=0.95, dark=0, reverse=True, rot=0.4,start=-.2, hue=0.6)

models_colors=["#83CCD2","#A7CDA8","#D6CE7E","#E69F63"]
heatmap_cmap = sns.blend_palette(["#17131C","#997BBA","#D2A8FF","#E7D4FC","#F4EEFA"],as_cmap=True)

plot_rc_pars = {"axes.labelsize":7, "font.size":6, "legend.fontsize":6, "xtick.labelsize":6, 
                                          "ytick.labelsize":6, "axes.titlesize":7, "legend.title_fontsize":7,
                                          "lines.markersize": 3, "axes.linewidth": 0.5,
                                            "xtick.major.width": 0.5, "ytick.major.width": 0.5, "xtick.minor.width": 0.5,
                                            "ytick.minor.width": 0.5, "xtick.major.size": 2, "ytick.major.size": 2,
                                            "xtick.minor.size": 1, "ytick.minor.size": 1, "legend.labelspacing": 0.2}
rc_pars={"xtick.major.pad": 1, "ytick.major.pad": 1, "legend.labelspacing": 0.2}
mpl.rcParams.update(rc_pars)

def plot_predictions(ifnb_predicted, beta, conditions, name, figures_dir, lines = True):
    df_ifnb_predicted = make_predictions_data_frame(ifnb_predicted, beta, conditions)
    col = sns.color_palette("rocket", n_colors=7)[4]
    col = mcolors.rgb2hex(col) 
    fig, ax = plt.subplots(figsize=(6, 6))
    
    sns.scatterplot(data=df_ifnb_predicted, x="Data point", y=r"IFN$\beta$", 
                    color="black", alpha=0.5, ax=ax, zorder = 1, label="Predicted")
    if lines:
        sns.lineplot(data=df_ifnb_predicted.loc[df_ifnb_predicted["par_set"] != "Data"], x="Data point", y=r"IFN$\beta$", 
                        units="par_set", color="black", estimator=None, ax=ax, legend=False, zorder = 2, alpha=0.2)
        sns.lineplot(data=df_ifnb_predicted.loc[df_ifnb_predicted["par_set"] == "Data"], x="Data point", y=r"IFN$\beta$",
                        color=col, estimator=None, ax=ax, legend=False, zorder = 3)
    sns.scatterplot(data=df_ifnb_predicted.loc[df_ifnb_predicted["par_set"] == "Data"], x="Data point", y=r"IFN$\beta$", 
                    color=col, marker="o", ax=ax, zorder = 4, label="Observed")
    xticks = ax.get_xticks()
    labels = [item.get_text().replace(" ", "\n") for item in ax.get_xticklabels()]
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels)
    sns.despine()
    plt.xticks(rotation=90)
    plt.tight_layout()
    sns.move_legend(ax, bbox_to_anchor=(1.05, 0.5), title=None, frameon=False, loc="center left")
    plt.savefig("%s/%s.png" % (figures_dir, name), bbox_inches="tight")
    plt.close()

def plot_parameters(pars, name, figures_dir):
    df_pars = pars.drop(columns=["h1", "h2", "h3", "rmsd"], errors="ignore")

    df_pars["par_set"] = np.arange(len(df_pars))
    df_pars = df_pars.melt(var_name="Parameter", value_name="Value", id_vars="par_set")
    # df_t_pars = df_pars[df_pars["Parameter"].str.startswith("t")]
    df_t_pars = df_pars.loc[df_pars["Parameter"].str.startswith("t")].copy()
    num_t_pars = len(df_t_pars["Parameter"].unique())
    new_t_par_names = [r"$t_{I_2}$", r"$t_{I_1}$", r"$t_N$", r"$t_{I_1I_2}$", r"$t_{I_1N}$"]
    # Rename t parameters
    df_t_pars["Parameter"] = df_t_pars["Parameter"].replace(["t1", "t2", "t3", "t4", "t5"], new_t_par_names)
    df_t_pars["Parameter"] = df_t_pars["Parameter"].replace(["t_1", "t_2", "t_3", "t_4", "t_5"], new_t_par_names)
    new_t_par_order = [r"$t_{I_1}$", r"$t_{I_2}$", r"$t_N$", r"$t_{I_1I_2}$", r"$t_{I_1N}$"]
    df_t_pars["Parameter"] = pd.Categorical(df_t_pars["Parameter"], categories=new_t_par_order, ordered=True)

    
    # df_k_pars = df_pars[df_pars["Parameter"].str.startswith("k")]
    df_k_pars = df_pars.loc[df_pars["Parameter"].str.startswith("k")].copy()
    num_k_pars = len(df_k_pars["Parameter"].unique())
    # df_k_pars["Parameter"] = df_k_pars["Parameter"].str.replace("k3", r"$k_N$")
    # df_k_pars["Parameter"] = df_k_pars["Parameter"].str.replace("k2", r"$k_2$")
    # df_k_pars["Parameter"] = df_k_pars["Parameter"].str.replace("k1", r"$k_1$")
    # df_k_pars["Parameter"] = df_k_pars["Parameter"].str.replace("kn", r"$k_N$")
    df_k_pars.loc[df_k_pars["Parameter"] == "k1", "Parameter"] = r"$k_{I_2}$" # Rename
    df_k_pars.loc[df_k_pars["Parameter"] == "k2", "Parameter"] = r"$k_{I_1}$" # Rename
    df_k_pars.loc[df_k_pars["Parameter"] == "kn", "Parameter"] = r"$k_N$"
    df_k_pars.loc[df_k_pars["Parameter"] == "k3", "Parameter"] = r"$k_N$"
    df_k_pars["Parameter"] = pd.Categorical(df_k_pars["Parameter"], categories=[r"$k_{I_1}$", r"$k_{I_2}$", r"$k_N$"], ordered=True)

    fig, ax = plt.subplots(1,2, figsize=(10,5), gridspec_kw={"width_ratios":[num_t_pars, num_k_pars]})
    sns.lineplot(data=df_t_pars, x="Parameter", y="Value", units="par_set", estimator=None, legend=False, alpha=0.2, ax=ax[0], color="black")
    sns.scatterplot(data=df_t_pars, x="Parameter", y="Value", color="black", ax=ax[0], legend=False, alpha=0.2, zorder = 10)
    sns.lineplot(data=df_k_pars, x="Parameter", y="Value", units="par_set", estimator=None, ax=ax[1], legend=False,alpha=0.2, color="black")
    sns.scatterplot(data=df_k_pars, x="Parameter", y="Value", color="black", ax=ax[1], legend=False, alpha=0.2, zorder = 10)
    ax[1].set_yscale("log")
    sns.despine()
    plt.tight_layout()
    plt.savefig("%s/%s.png" % (figures_dir, name))
    plt.close()

def make_predictions_data_frame(ifnb_predicted, beta, conditions):
    df_ifnb_predicted = pd.DataFrame(ifnb_predicted, columns=conditions)
    df_ifnb_predicted["par_set"] = np.arange(len(df_ifnb_predicted))
    df_ifnb_predicted = df_ifnb_predicted.melt(var_name="Data point", value_name=r"IFN$\beta$", id_vars="par_set")

    df_ifnb_predicted_data = pd.DataFrame({"Data point":conditions, r"IFN$\beta$":beta, "par_set":"Data"})
    df_ifnb_predicted = pd.concat([df_ifnb_predicted, df_ifnb_predicted_data], ignore_index=True)

    df_ifnb_predicted["Stimulus"] = df_ifnb_predicted["Data point"].str.split("_", expand=True)[0]
    df_ifnb_predicted["Stimulus"] = df_ifnb_predicted["Stimulus"].replace("polyIC", "PolyIC")

    df_ifnb_predicted["Genotype"] = df_ifnb_predicted["Data point"].str.split("_", expand=True)[1]
    df_ifnb_predicted["Category"] = "Stimulus specific"
    df_ifnb_predicted.loc[df_ifnb_predicted["Genotype"].str.contains("rela"), "Category"] = "NFκB dependence"
    df_ifnb_predicted.loc[df_ifnb_predicted["Genotype"].str.contains("irf"), "Category"] = "IRF dependence"
    df_ifnb_predicted.loc[df_ifnb_predicted["Genotype"].str.contains("p50"), "Category"] = "p50 dependence"

    df_ifnb_predicted["Genotype"] = df_ifnb_predicted["Genotype"].replace("relacrelKO", r"NFκBko")
    df_ifnb_predicted["Genotype"] = df_ifnb_predicted["Genotype"].replace("irf3irf7KO", "IRF3/7ko")
    df_ifnb_predicted["Genotype"] = df_ifnb_predicted["Genotype"].replace("irf3irf5irf7KO", "IRF3/5/7ko")
    df_ifnb_predicted["Genotype"] = df_ifnb_predicted["Genotype"].replace("p50KO", "p50ko")
    df_ifnb_predicted["Data point"] = df_ifnb_predicted["Stimulus"] + " " + df_ifnb_predicted["Genotype"]    
    stimuli_levels = ["basal", "CpG", "LPS", "PolyIC"]
    # genotypes_levels = ["WT", "irf3irf7KO", "irf3irf5irf7KO", "relacrelKO"]
    genotypes_levels = ["WT","p50ko", "IRF3/7ko", "IRF3/5/7ko", r"NFκBko"]
    df_ifnb_predicted["Stimulus"] = pd.Categorical(df_ifnb_predicted["Stimulus"], categories=stimuli_levels, ordered=True)
    df_ifnb_predicted["Genotype"] = pd.Categorical(df_ifnb_predicted["Genotype"], categories=genotypes_levels, ordered=True)
    df_ifnb_predicted = df_ifnb_predicted.sort_values(["Stimulus", "Genotype"])
    # print(df_ifnb_predicted)
    return df_ifnb_predicted

def fix_ax_labels(ax, is_heatmap=False):
    # print([item.get_text().split(" ")[1] for item in ax.get_xticklabels()])
    labels_genotype_only = [item.get_text().split(" ")[1] for item in ax.get_xticklabels()]
    # ax.set_xticklabels(labels_genotype_only)
    labels_stimulus_only = [item.get_text().split(" ")[0] for item in ax.get_xticklabels()]
    unique_gens= np.unique(labels_genotype_only)

    gens_locations = {gen: np.where(np.array(labels_genotype_only) == gen)[0] for gen in unique_gens}
    gens_mean_locs = [np.mean(locations) for gen, locations in gens_locations.items()]
    gens_mean_locs = [loc + 10**-5 for loc in gens_mean_locs]
    xticks = ax.get_xticks()
    # xticks = xticks + gens_mean_locs
    if is_heatmap:
        gens_mean_locs = [loc + 0.5 for loc in gens_mean_locs]
    xticks = np.concatenate((xticks, gens_mean_locs))
    # print(xticks)
    unique_gens = ["\n\n%s" % gen for gen in unique_gens]
    labels = labels_stimulus_only + unique_gens
    ax.set_xticks(xticks)
    ax.set_xticklabels(labels)
    ax.set_xlabel("")

    for label in ax.get_xticklabels():
        label.set_rotation(0)

    # Get all xticks
    xticks = ax.xaxis.get_major_ticks()

    # Remove the tick lines for the last three xticks
    for tick in xticks[len(labels_genotype_only):]:
        tick.tick1line.set_visible(False)
        tick.tick2line.set_visible(False)

    return ax, labels_genotype_only

def make_predictions_plot(df_all, name, figures_dir):
    # Plot separately
    for category in df_all["Category"].unique():
        
        with sns.plotting_context("paper", rc=plot_rc_pars):
            num_bars = len(df_all[df_all["Category"]==category]["Data point"].unique())
            width  = 3.1*num_bars/3/2.1
            height = 1.3/1.7
            fig, ax = plt.subplots(figsize=(width, height))
            cols = [data_color] + models_colors
            sns.barplot(data=df_all[df_all["Category"]==category], x="Data point", y=r"IFN$\beta$", hue="Hill", 
                        palette=cols, ax=ax, width=0.8, errorbar=None, legend=False, saturation=.9, 
                        linewidth=0.5, edgecolor="black", err_kws={'linewidth': 0.75, "color":"black"})
            sns.stripplot(data=df_all[(df_all["Category"]==category)&(~(df_all["par_set"] == "Data"))], x="Data point", y=r"IFN$\beta$", 
                          hue="Hill", alpha=0.5, ax=ax, size=1.5, jitter=True, dodge=True, palette="dark:black", legend=False)
            ax.set_xlabel("")
            ax.set_ylabel(r"$IFN\beta\ f$")
            # ax.set_title(category)
            sns.despine()
            ax, _ = fix_ax_labels(ax)
            plt.tight_layout(pad=0)
            plt.ylim(0,1)
            category_nospace = category.replace(" ", "-")
            plt.savefig("%s/%s_%s.png" % (figures_dir, name, category_nospace), bbox_inches="tight")
            plt.close()

    # Make one plot with legend
    with sns.plotting_context("paper", rc=plot_rc_pars):
            category = "NFκB dependence"
            num_bars = len(df_all[df_all["Category"]==category]["Data point"].unique())
            width  = 3.1*num_bars/3/2.1 + 0.5
            height = 1.3/1.7
            fig, ax = plt.subplots(figsize=(width, height))
            cols = [data_color] + models_colors
            sns.barplot(data=df_all[df_all["Category"]==category], x="Data point", y=r"IFN$\beta$", hue="Hill", 
                        palette=cols, ax=ax, width=0.8, errorbar="sd", saturation=.9, 
                        linewidth=0.5, edgecolor="black", err_kws={'linewidth': 0.75})
            ax.set_xlabel("")
            ax.set_ylabel(r"IFN$\beta$")
            # ax.set_title(category)
            sns.despine()
            ax, _ = fix_ax_labels(ax)
            plt.tight_layout(pad=0)
            plt.ylim(0,1)
            sns.move_legend(ax, bbox_to_anchor=(1,1), title=None, frameon=False, loc="upper left", ncol=1)
            plt.savefig("%s/%s_legend.png" % (figures_dir, name), bbox_inches="tight")
            plt.close()

def plot_predictions_one_plot(ifnb_predicted_1, h1, ifnb_predicted_2, h2, ifnb_predicted_3, h3, ifnb_predicted_4, h4, beta, conditions, name, figures_dir, hn=None):
    # Plot predictions for all conditions in one plot. Average of best 20 models for each hill combination with error bars.
    df_ifnb_predicted_1 = make_predictions_data_frame(ifnb_predicted_1, beta, conditions)
    df_ifnb_predicted_2 = make_predictions_data_frame(ifnb_predicted_2, beta, conditions)
    df_ifnb_predicted_3 = make_predictions_data_frame(ifnb_predicted_3, beta, conditions)
    df_ifnb_predicted_4 = make_predictions_data_frame(ifnb_predicted_4, beta, conditions)

    data_df = df_ifnb_predicted_1.loc[df_ifnb_predicted_1["par_set"] == "Data"].copy()

    df_sym = pd.concat([df_ifnb_predicted_1, 
                        df_ifnb_predicted_2,
                        df_ifnb_predicted_3,
                        df_ifnb_predicted_4], ignore_index=True)
    df_sym = pd.concat([df_ifnb_predicted_1, df_ifnb_predicted_2, df_ifnb_predicted_3, df_ifnb_predicted_4], ignore_index=True)
    df_sym[r"H_I"] = np.concatenate([np.repeat(h1, len(df_ifnb_predicted_1)), np.repeat(h2, len(df_ifnb_predicted_2)),
                                        np.repeat(h3, len(df_ifnb_predicted_3)), np.repeat(h4, len(df_ifnb_predicted_4))])
    
    if hn is not None:
        hn_1, hn_2, hn_3, hn_4 = [str(h) for h in hn]

        df_sym[r"H_N"] = np.concatenate([np.repeat(hn_1, len(df_ifnb_predicted_1)), np.repeat(hn_2, len(df_ifnb_predicted_2)),
                                        np.repeat(hn_3, len(df_ifnb_predicted_3)), np.repeat(hn_4, len(df_ifnb_predicted_4))])
        df_sym["Hill"] = r"$h_{I}$=" + df_sym[r"H_I"] + r", $h_{N}$=" + df_sym[r"H_N"]
    else:
        df_sym["Hill"] = r"$h_{I}$=" + df_sym[r"H_I"]
    
    # data_df[r"H_{I_2}"] = np.repeat("Data", len(data_df))
    # data_df[r"H_{I_1}"] = np.repeat("", len(data_df))
    data_df[r"H_I"] = np.repeat("Data", len(data_df))
    data_df["Hill"] = "Exp."

    df_sym = df_sym.loc[df_sym["par_set"] != "Data"] # contains duplicate data points
    df_all = pd.concat([df_sym, data_df], ignore_index=True)

    hill_categories = np.concatenate([data_df["Hill"].unique(), df_sym["Hill"].unique()])

    df_all["Hill"] = pd.Categorical(df_all["Hill"], categories=hill_categories, ordered=True)
    make_predictions_plot(df_all, name, figures_dir)


def plot_predictions_one_plot_with_data(ifnb_predicted_1, h1, ifnb_predicted_2, h2, ifnb_predicted_3, h3, ifnb_predicted_4, h4, 
                                        training_data, name, figures_dir, data_only=False):
    # Plot predictions for all conditions in one plot. Average of best 20 models for each hill combination with error bars.
    beta = training_data["IFNb"]
    conditions = training_data["Stimulus"] + "_" + training_data["Genotype"]
    training_data["Condition"] = pd.Categorical(conditions, categories=conditions.unique(), ordered=True)
    df_ifnb_predicted_1 = make_predictions_data_frame(ifnb_predicted_1, beta, conditions)
    df_ifnb_predicted_2 = make_predictions_data_frame(ifnb_predicted_2, beta, conditions)
    df_ifnb_predicted_3 = make_predictions_data_frame(ifnb_predicted_3, beta, conditions)
    df_ifnb_predicted_4 = make_predictions_data_frame(ifnb_predicted_4, beta, conditions)

    data_df = df_ifnb_predicted_1.loc[df_ifnb_predicted_1["par_set"] == "Data"].copy()

    df_all = pd.concat([df_ifnb_predicted_1, df_ifnb_predicted_2, df_ifnb_predicted_3, df_ifnb_predicted_4], ignore_index=True)
    
    df_all[r"H_I"] = np.concatenate([np.repeat(h1, len(df_ifnb_predicted_1)), np.repeat(h2, len(df_ifnb_predicted_2)),
                                        np.repeat(h3, len(df_ifnb_predicted_3)), np.repeat(h4, len(df_ifnb_predicted_4))])
    df_all["Hill"] =r"$h_{I}$=" + df_all[r"H_I"]
    
    data_df[r"H_I"] = np.repeat("Data", len(data_df))
    data_df["Hill"] = "Experimental"

    df_all = df_all.loc[df_all["par_set"] != "Data"] # contains duplicate data points
    df_all = pd.concat([df_all, data_df], ignore_index=True)
    
    new_rc_pars = plot_rc_pars.copy()
    rc_dict = {"legend.fontsize":5,"legend.labelspacing":0.1}
    new_rc_pars.update(rc_dict)
    with sns.plotting_context("paper",rc=new_rc_pars):
        colors = models_colors
        col = data_color
        fig, ax = plt.subplots(2, 1, figsize=(2.3,2.7), gridspec_kw={"height_ratios": [4, 2]})
        # sns.lineplot(data=df_all.loc[df_all["par_set"] != "Data"], x="Data point", y=r"IFN$\beta$", hue="Hill", palette=colors, 
        #              ax=ax, err_style="band", errorbar=("pi",50), zorder = 0)
        # sns.scatterplot(data=df_all.loc[df_all["par_set"] != "Data"], x="Data point", y=r"IFN$\beta$", hue="Hill", palette=colors, marker="o", ax=ax, 
        #                 legend=False, linewidth=0,  zorder = 1)
        
        df_sub = df_all.loc[df_all["par_set"] != "Data"]
        unique_hills = np.unique(df_sub["Hill"])

        if not data_only:
            # Plot predictions
            for i, hill in enumerate(unique_hills):
                # Filter data for the current Hill
                df_hill = df_all[df_all["Hill"] == hill]

                # Create lineplot and scatterplot for the current Hill
                sns.lineplot(data=df_hill.loc[df_hill["par_set"] != "Data"], x="Data point", y=r"IFN$\beta$", color=colors[i], 
                            ax=ax[0], err_style="band", errorbar=("pi",50), zorder = i, label=hill)
                sns.scatterplot(data=df_hill.loc[df_hill["par_set"] != "Data"], x="Data point", y=r"IFN$\beta$", color=colors[i],
                            marker="o", ax=ax[0], linewidth=0,  zorder = i+0.5)


        sns.lineplot(data=df_all.loc[df_all["par_set"] == "Data"], x="Data point", y=r"IFN$\beta$", color=col, ax=ax[0], 
                     label="Experimental", zorder = 10)
        sns.scatterplot(data=df_all.loc[df_all["par_set"] == "Data"], x="Data point", y=r"IFN$\beta$", color=col, marker="o", 
                        ax=ax[0], legend=False, linewidth=0, zorder = 11)
        
        # Plot training data
        # Pivot so that IRF and NFKB column names go to "protein" and the values go to "concentration"
        training_data_pivot = training_data.loc[:, ["Condition", "IRF", "NFkB"]]
        training_data_pivot = training_data_pivot.melt(id_vars="Condition", var_name="Protein", value_name="Concentration")
        training_data_pivot["Protein"] = training_data_pivot["Protein"].replace({"IRF": r"$IRF$", "NFkB": r"$NF\kappa B$"})
        # Make wide so that protein is index and condition is columns
        training_data_pivot = training_data_pivot.pivot(index="Protein", columns="Condition", values="Concentration")

        sns.heatmap(training_data_pivot, vmin=0, vmax=1, cmap=heatmap_cmap, cbar_kws={"label": "Concentration"}, annot=True, 
                    fmt=".2f", annot_kws={"size": 5}, ax=ax[1])

        # Labels
        xticks = ax[0].get_xticks()
        labels_genotype_only = [item.get_text().split(" ")[1] for item in ax[0].get_xticklabels()]
        # ax.set_xticklabels(labels_genotype_only) # for testing
        labels_stimulus_only = [item.get_text().split(" ")[0] for item in ax[0].get_xticklabels()]
        unique_stimuli = np.unique(labels_stimulus_only)
        stimuli_locations = {stimulus: np.where(np.array(labels_stimulus_only) == stimulus)[0] for stimulus in unique_stimuli}
        stimuli_mean_locs = [np.mean(locations) for stimulus, locations in stimuli_locations.items()]
        stimuli_mean_locs = [loc + 10**-5 for loc in stimuli_mean_locs]
        xticks = xticks + stimuli_mean_locs
        unique_stimuli = ["\n\n\n\n\n\n%s" % stimulus for stimulus in unique_stimuli]
        labels = labels_genotype_only + unique_stimuli

        ax[0].set_xticklabels("")
        ax[0].set_xticks([])

        xticks = [x + 0.5 for x in xticks]
        ax[1].set_xticks(xticks)
        ax[1].set_xticklabels(labels)
        ax[1].set_ylabel("Input")
        ax[1].set_xlabel("")
        cbar = ax[1].collections[0].colorbar
        cbar.remove()
        ax[0].set_xlabel("")

        for label in ax[1].get_xticklabels():
            if label.get_text() in labels_genotype_only:
                label.set_rotation(90)
            else:
                label.set_rotation(0)

        # Get all xticks
        xticks = ax[1].xaxis.get_major_ticks()

        # Remove the tick lines for the last three xticks
        for tick in xticks[len(labels_genotype_only):]:
            tick.tick1line.set_visible(False)
            tick.tick2line.set_visible(False)

        sns.despine()
        plt.tight_layout()
        sns.move_legend(ax[0], bbox_to_anchor=(0.5,1), title=None, frameon=False, loc="lower center", ncol=3)
        plt.savefig("%s/%s.png" % (figures_dir, name), bbox_inches="tight")
        plt.close()

def make_parameters_data_frame(pars):
    df_pars = pars.drop(columns=["h1", "h2", "h3", "rmsd"], errors="ignore")

    df_pars["par_set"] = np.arange(len(df_pars))
    # Make columns t_0=0 and t_IN=1
    df_pars["t_0"] = 0
    df_pars["t_IN"] = 1
    df_pars = df_pars.melt(var_name="Parameter", value_name="Value", id_vars="par_set")
    # df_t_pars = df_pars[df_pars["Parameter"].str.startswith("t")]
    df_t_pars = df_pars.loc[df_pars["Parameter"].str.startswith("t")].copy()
    num_t_pars = len(df_t_pars["Parameter"].unique())
    new_t_par_names = [r"$t_I$", r"$t_N$", "error","error", "error"]
    # Rename t parameters
    df_t_pars["Parameter"] = df_t_pars["Parameter"].replace(["t1", "t2", "t3", "t4", "t5"], new_t_par_names)
    df_t_pars["Parameter"] = df_t_pars["Parameter"].replace(["t_1", "t_2", "t_3", "t_4", "t_5"], new_t_par_names)
    df_t_pars["Parameter"] = df_t_pars["Parameter"].replace(["t_0", "t_IN"], [r"$t_0$", r"$t_{IN}$"])
    new_t_par_order = [r"$t_0$",r"$t_I$", r"$t_N$", r"$t_{IN}$"]
    df_t_pars["Parameter"] = pd.Categorical(df_t_pars["Parameter"], categories=new_t_par_order, ordered=True)

    
    # df_k_pars = df_pars[df_pars["Parameter"].str.startswith("k")]
    df_k_pars = df_pars.loc[df_pars["Parameter"].str.startswith("k") | df_pars["Parameter"].str.startswith("c")].copy()
    num_k_pars = len(df_k_pars["Parameter"].unique())
    
    df_k_pars.loc[df_k_pars["Parameter"] == "k1", "Parameter"] = r"$k_I$" # Rename
    df_k_pars.loc[df_k_pars["Parameter"] == "k2", "Parameter"] = r"$K_N$" # Rename
    df_k_pars.loc[df_k_pars["Parameter"] == "c", "Parameter"] = r"$C$"
    df_k_pars["Parameter"] = pd.Categorical(df_k_pars["Parameter"], categories=[r"$k_I$", r"$K_N$", r"$C$"], ordered=True)
    return df_t_pars, df_k_pars, num_t_pars, num_k_pars

def make_ki_plot(df_ki_pars, name, figures_dir):
    df_ki_pars = df_ki_pars.loc[df_ki_pars["Parameter"] == r"$k_I$"]
    IRF_array = np.arange(0, 1.1, 0.05)
    # Duplicate the dataframe for each value of IRF
    df_ki_pars = pd.concat([df_ki_pars]*len(IRF_array), ignore_index=True)
    df_ki_pars["IRF"] = np.repeat(IRF_array, len(df_ki_pars)/len(IRF_array))
    df_ki_pars[r"$h_I$"] = df_ki_pars["H_I"].astype(int)
    df_ki_pars[r"$K_I$"] = df_ki_pars["Value"]*df_ki_pars["IRF"]**(df_ki_pars[r"$h_I$"]-1)
    
    colors = models_colors
    with sns.plotting_context("paper", rc=plot_rc_pars):
        fig, ax = plt.subplots(figsize=(2.1,1.5))
        sns.lineplot(data=df_ki_pars, x="IRF", y=r"$K_I$", hue=r"$h_I$", palette=colors, ax=ax, zorder = 0,  errorbar=None, estimator=None, alpha=0.2, units="par_set")
        # sns.scatterplot(data=df_ki_pars,x="IRF", y=r"$K_I$", hue=r"$h_I$", palette=colors, ax=ax, legend=False, zorder = 1, linewidth=0, alpha=0.2)
        ax.set_xlabel(r"$[IRF]$ (MNU)")
        ax.set_ylabel(r"$k_I [IRF]^{h_I-1}$ (MNU$^{-1}$)")
        sns.despine()
        sns.move_legend(ax, loc='center left', bbox_to_anchor=(1, 0.5), frameon=False,
                        columnspacing=1, handletextpad=0.5, handlelength=1.5)
        plt.tight_layout()

        # Change alpha of legend
        leg = ax.get_legend()
        for line in leg.get_lines():
            line.set_alpha(1)

        plt.savefig("%s/%s.png" % (figures_dir, name), bbox_inches="tight")
        plt.close()

    # Log scale
    with sns.plotting_context("paper", rc=plot_rc_pars):
        fig, ax = plt.subplots(figsize=(2.1,1.5))
        sns.lineplot(data=df_ki_pars, x="IRF", y=r"$K_I$", hue=r"$h_I$", palette=colors, ax=ax, zorder = 0,  errorbar=None, estimator=None, alpha=0.2, units="par_set")
        # sns.scatterplot(data=df_ki_pars,x="IRF", y=r"$K_I$", hue=r"$h_I$", palette=colors, ax=ax, legend=False, zorder = 1, linewidth=0, alpha=0.2)
        ax.set_xlabel(r"$[IRF]$ (MNU)")
        ax.set_ylabel(r"$k_I [IRF]^{h_I-1}$ (MNU$^{-1}$)")
        ax.set_yscale("log")
        sns.despine()
        sns.move_legend(ax, loc='center left', bbox_to_anchor=(1, 0.5), frameon=False,
                        columnspacing=1, handletextpad=0.5, handlelength=1.5)
        plt.tight_layout()

        # Change alpha of legend
        leg = ax.get_legend()
        for line in leg.get_lines():
            line.set_alpha(1)

        plt.savefig("%s/%s_log.png" % (figures_dir, name), bbox_inches="tight")
        plt.close()

    # Log-log scale
    with sns.plotting_context("paper", rc=plot_rc_pars):
        fig, ax = plt.subplots(figsize=(2.1,1.5))
        sns.lineplot(data=df_ki_pars, x="IRF", y=r"$K_I$", hue=r"$h_I$", palette=colors, ax=ax, zorder = 0,  errorbar=None, estimator=None, alpha=0.2, units="par_set")
        # sns.scatterplot(data=df_ki_pars,x="IRF", y=r"$K_I$", hue=r"$h_I$", palette=colors, ax=ax, legend=False, zorder = 1, linewidth=0, alpha=0.2)
        ax.set_xlabel(r"$[IRF]$ (MNU)")
        ax.set_ylabel(r"$k_I [IRF]^{h_I-1}$ (MNU$^{-1}$)")
        ax.set_xscale("log")
        ax.set_yscale("log")
        sns.despine()
        sns.move_legend(ax, loc='center left', bbox_to_anchor=(1, 0.5), frameon=False,
                        columnspacing=1, handletextpad=0.5, handlelength=1.5)
        plt.tight_layout()

        # Change alpha of legend
        leg = ax.get_legend()
        for line in leg.get_lines():
            line.set_alpha(1)

        plt.savefig("%s/%s_log_log.png" % (figures_dir, name), bbox_inches="tight")
        plt.close()

def make_pars_plots(num_t_pars, num_k_pars, df_all_t_pars, df_all_k_pars, name, figures_dir):
    colors = models_colors
    width = 2.1
    height = 1
    fig, ax = plt.subplots(1,2, figsize=(width, height), 
                            gridspec_kw={"width_ratios":[num_t_pars, num_k_pars]})
    
    k_parameters = [r"$K_N$"] # Only plot K_N

    unique_models = np.unique(df_all_t_pars["Model"])

    all_parameters = df_all_k_pars["Parameter"].unique()
    if (r"$C$" in all_parameters) or ("C" in all_parameters):
        has_c=True
    else:
        has_c=False

    with sns.plotting_context("paper",rc=plot_rc_pars):
        width = 2.8
        height = 1
        if has_c:
            fig, ax = plt.subplots(1,3, figsize=(width, height), 
                               gridspec_kw={"width_ratios":[num_t_pars, 1, 1]})
        else:
            fig, ax = plt.subplots(1,2, figsize=(width, height), 
                                gridspec_kw={"width_ratios":[num_t_pars, 1]})
        unique_models = np.unique(df_all_t_pars["Model"])
        legend_handles = []

        s = sns.stripplot(data=df_all_t_pars, x="Parameter", y="Value", hue = "Model", palette=colors, ax=ax[0], zorder = 0, linewidth=0,
                            alpha=0.2, jitter=0, dodge=True, legend=False)
        
        legend_handles = s.collections
       
        df2 = df_all_k_pars[(df_all_k_pars["Parameter"].isin(k_parameters))]
        df2 = df2.copy()
        df2["Parameter"] = df2["Parameter"].cat.remove_unused_categories()
        s = sns.stripplot(data=df2, x="Parameter", y="Value", hue = "Model", palette=colors, ax=ax[1], zorder = 0, linewidth=0, 
                          alpha=0.2, jitter=0, dodge=True, legend=False)

        ax[1].set_yscale("log")
        ax[1].set_ylabel(r"Value (MNU$^{-1}$)")

        if has_c:
            df2 = df_all_k_pars[(df_all_k_pars["Parameter"].isin(["C",r"$C$"]))]
            df2 = df2.copy()
            df2["Parameter"] = df2["Parameter"].cat.remove_unused_categories()
            s = sns.stripplot(data=df2, x="Parameter", y="Value", hue = "Model", palette=colors, ax=ax[2], zorder = 0, linewidth=0, 
                          alpha=0.2, jitter=0, dodge=True, legend=False)
            ax[2].set_yscale("log")
            ax[2].set_ylabel(r"Value")
            ax[2].set_xlabel("")
            ax[2].set_ylim(ax[1].get_ylim())
        

        ax[0].set_ylabel("Parameter Value")
        
        for x in ax[0], ax[1]:
            x.set_xlabel("")

        sns.despine()
        plt.tight_layout()

        leg = fig.legend(legend_handles, unique_models, loc="lower center", bbox_to_anchor=(0.5, 1), frameon=False, 
                         ncol=4, columnspacing=1, handletextpad=0.5, handlelength=1.5)

        for i in range(len(leg.legend_handles)):
            leg.legend_handles[i].set_alpha(1)
            leg.legend_handles[i].set_color(colors[i])


        plt.savefig("%s/%s.png" % (figures_dir, name), bbox_inches="tight")
        plt.close()

        make_ki_plot(df_all_k_pars, name + "_k_i", figures_dir)

# Plot parameters one plot
def plot_parameters_one_plot(pars_1, hi_1, pars_2, hi_2, pars_3, hi_3, pars_4, hi_4, name, figures_dir, hn=None):
    df_t_pars_1, df_k_pars_1, _, _ = make_parameters_data_frame(pars_1)
    df_t_pars_2, df_k_pars_2, _, _ = make_parameters_data_frame(pars_2)
    df_t_pars_3, df_k_pars_3, _, _ = make_parameters_data_frame(pars_3)
    df_t_pars_4, df_k_pars_4, num_t_pars, num_k_pars = make_parameters_data_frame(pars_4)

    df_all_t_pars = pd.concat([df_t_pars_1, df_t_pars_2, df_t_pars_3, df_t_pars_4], ignore_index=True)
    df_all_k_pars = pd.concat([df_k_pars_1, df_k_pars_2, df_k_pars_3, df_k_pars_4], ignore_index=True)

    df_all_t_pars[r"H_I"] = np.concatenate([np.repeat(hi_1, len(df_t_pars_1)), np.repeat(hi_2, len(df_t_pars_2)),
                                        np.repeat(hi_3, len(df_t_pars_3)), np.repeat(hi_4, len(df_t_pars_4))])
    df_all_k_pars[r"H_I"] = np.concatenate([np.repeat(hi_1, len(df_k_pars_1)), np.repeat(hi_2, len(df_k_pars_2)),
                                        np.repeat(hi_3, len(df_k_pars_3)), np.repeat(hi_4, len(df_k_pars_4))])
    
    if hn is not None:
        hn_1, hn_2, hn_3, hn_4 = [str(h) for h in hn]

        df_all_t_pars[r"H_N"] = np.concatenate([np.repeat(hn_1, len(df_t_pars_1)), np.repeat(hn_2, len(df_t_pars_2)),
                                        np.repeat(hn_3, len(df_t_pars_3)), np.repeat(hn_4, len(df_t_pars_4))])
        df_all_k_pars[r"H_N"] = np.concatenate([np.repeat(hn_1, len(df_k_pars_1)), np.repeat(hn_2, len(df_k_pars_2)),
                                        np.repeat(hn_3, len(df_k_pars_3)), np.repeat(hn_4, len(df_k_pars_4))])
        
        df_all_t_pars["Model"] = r"$h_{I}$=" + df_all_t_pars[r"H_I"] + r", $h_{N}$=" + df_all_t_pars[r"H_N"]
        df_all_k_pars["Model"] = r"$h_{I}$=" + df_all_k_pars[r"H_I"] + r", $h_{N}$=" + df_all_k_pars[r"H_N"] 
    else:
        df_all_t_pars["Model"] = r"$h_{I}$=" + df_all_t_pars[r"H_I"]
        df_all_k_pars["Model"] = r"$h_{I}$=" + df_all_k_pars[r"H_I"]


    make_pars_plots(num_t_pars, num_k_pars, df_all_t_pars, df_all_k_pars, name, figures_dir)
    

def calculate_ifnb(pars, data):
    num_t_pars = 2
    num_k_pars = 2
    num_h_pars = 2
    t_pars, k_pars, h_pars = pars[:num_t_pars], pars[num_t_pars:num_t_pars+num_k_pars], pars[num_t_pars+num_k_pars:num_t_pars+num_k_pars+num_h_pars]
    N, I = data["NFkB"], data["IRF"]
    ifnb = [get_f(n,i, model=None, t=t_pars, k=k_pars, h=h_pars, C=1) for n,i in zip(N,I)]
    ifnb = np.array(ifnb)
    return ifnb

def make_param_scan_plots():
    figures_dir = "two_site_final_figures"
    os.makedirs(figures_dir, exist_ok=True)
    model = "two_site"
    training_data = pd.read_csv("../data/training_data.csv")
    beta = training_data["IFNb"]
    conditions = training_data["Stimulus"] + "_" + training_data["Genotype"]
    h_values = np.meshgrid([1,3], [1,3], [1,3])
    h_values = np.array(h_values).T.reshape(-1,3)

    results_dir = "parameter_scan/"

    # Load best parameters
    print("Plotting best-fit parameters for all hill combinations on one plot", flush=True)
    best_20_pars_df_1_1 = pd.read_csv("%s/results_h_1_1/%s_best_fits_pars.csv" % (results_dir, model))
    best_20_pars_df_2_1 = pd.read_csv("%s/results_h_2_1/%s_best_fits_pars.csv" % (results_dir, model))
    best_20_pars_df_3_1 = pd.read_csv("%s/results_h_3_1/%s_best_fits_pars.csv" % (results_dir, model))
    best_20_pars_df_4_1 = pd.read_csv("%s/results_h_4_1/%s_best_fits_pars.csv" % (results_dir, model))
    plot_parameters_one_plot(best_20_pars_df_1_1, "1", best_20_pars_df_2_1, "2", best_20_pars_df_3_1, "3", best_20_pars_df_4_1, "4",
                              "best_20_pars_IRF_hill", figures_dir)
    del best_20_pars_df_1_1, best_20_pars_df_2_1, best_20_pars_df_3_1, best_20_pars_df_4_1
    
    # Calculate ifnb predictions
    print("Plotting best-fit predictions for all hill combinations on one plot", flush=True)
    predictions_1_1 = np.loadtxt("%s/results_h_1_1/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    predictions_2_1 = np.loadtxt("%s/results_h_2_1/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    predictions_3_1 = np.loadtxt("%s/results_h_3_1/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    predictions_4_1 = np.loadtxt("%s/results_h_4_1/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")

    plot_predictions_one_plot(predictions_1_1, "1", predictions_2_1, "2", predictions_3_1, "3", predictions_4_1, "4", beta, conditions, 
                              "best_20_predictions_IRF_hill", figures_dir)
    del predictions_1_1, predictions_2_1, predictions_3_1, predictions_4_1  

    # Load best parameters with NFkB scan
    print("Plotting best-fit parameters for all hill combinations on one plot", flush=True)
    best_20_pars_df_1_1 = pd.read_csv("%s/results_h_1_1/%s_best_fits_pars.csv" % (results_dir, model))
    best_20_pars_df_1_3 = pd.read_csv("%s/results_h_1_3/%s_best_fits_pars.csv" % (results_dir, model))
    best_20_pars_df_3_1 = pd.read_csv("%s/results_h_3_1/%s_best_fits_pars.csv" % (results_dir, model))
    best_20_pars_df_3_3 = pd.read_csv("%s/results_h_3_3/%s_best_fits_pars.csv" % (results_dir, model))
    plot_parameters_one_plot(best_20_pars_df_1_1, "1", best_20_pars_df_1_3, "1", best_20_pars_df_3_1, "3", best_20_pars_df_3_3, "3",
                              "best_20_pars_I_N_hill", figures_dir, [1,3,1,3])
    del best_20_pars_df_1_1, best_20_pars_df_1_3, best_20_pars_df_3_1, best_20_pars_df_3_3


    # Calculate ifnb predictions with NFkB scan
    predictions_1_1 = np.loadtxt("%s/results_h_1_1/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    predictions_1_3 = np.loadtxt("%s/results_h_1_3/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    predictions_3_1 = np.loadtxt("%s/results_h_3_1/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    predictions_3_3 = np.loadtxt("%s/results_h_3_3/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    plot_predictions_one_plot(predictions_1_1, "1", predictions_1_3, "1", predictions_3_1, "3", predictions_3_3, "3", beta, conditions, 
                              "best_20_predictions_I_N_hill", figures_dir, [1,3,1,3])
    del predictions_1_1, predictions_1_3, predictions_3_1, predictions_3_3   

   
    print("Finished making param scan plots")

def get_max_residual(ifnb_predictions, beta, conditions):
    # Returns df with maximum residual for each par set
    df = make_predictions_data_frame(ifnb_predictions, beta, conditions)
    df_data_only = df.loc[df["par_set"] == "Data",["Data point", r"IFN$\beta$"]]
    df_data_only["Data point"] = pd.Categorical(df_data_only["Data point"], ordered=True)
    df_predictions_only = df.loc[~(df["par_set"] == "Data"),["par_set", "Data point", r"IFN$\beta$"]]
    df_combine = pd.merge(df_data_only, df_predictions_only, on="Data point", suffixes=(" data", " predictions"))
    df_combine["abs_residual"] = np.abs(df_combine[r"IFN$\beta$ predictions"] - df_combine[r"IFN$\beta$ data"])
    df_max = df_combine.loc[df_combine.groupby("par_set")["abs_residual"].idxmax()]
    # columns: Data point, IFN$\beta$ data, par_set, IFN$\beta$ predictions, abs_residual
    return df_max

def plot_max_resid(df, figures_dir, name=""):
    data_point_list= "../max_resid_data_points.csv"
    if os.path.exists(data_point_list):
        print("Loading existing data point list")
        data_points = pd.read_csv(data_point_list)
        new_data_points = [dp for dp in df["Data point"].unique() if dp not in data_points["Data point"].values]
        if len(new_data_points) > 0:
            data_points = pd.concat([data_points, pd.DataFrame({"Data point": new_data_points,
                                                               "Color": [None] * len(new_data_points)})], ignore_index=True)
    else:
        print("Creating new data point list")
        data_points = df.loc[:,["Data point"]]
        print(data_points)
        data_points = data_points.drop_duplicates()
        data_points.sort_values(by="Data point", inplace=True)

    pal = sns.cubehelix_palette(n_colors=len(data_points), light=0.8, dark=0.2, reverse=True, rot=1.4, start=1, hue=0.6)
    data_points["Color"] = pal
    data_points.to_csv(data_point_list, index=False)

    colors_dict = dict(data_points.values)

    # Sort by Cooperativity, then hI, then hN
    sort_order = ["Cooperativity", r"$h_I$", r"$h_N$"]
    df = df.sort_values(by=sort_order)
    df["model"] = pd.Categorical(df["model"], categories=df["model"].unique(), ordered=True)

    with sns.plotting_context("paper", rc=plot_rc_pars):
        fig, ax = plt.subplots(figsize=(3.8,1.5))
        sns.stripplot(data=df, x="model", y="abs_residual", hue="Data point", size=3, palette=colors_dict)

        ax.set_ylabel("Max Absolute Residual")
        plt.xticks(rotation=90)
        # sns.move_legend(ax, bbox_to_anchor=(0.5, 1), title="Worst-fit condition", frameon=False, loc="lower center", ncol=2)
        sns.move_legend(ax, bbox_to_anchor=(1, 0.5), title="Worst-fit condition", frameon=False, loc="center left", ncol=1)

        # Remove x-axis labels
        ax.set_xticklabels([])
        # Remove x-axis title
        ax.set_xlabel("")
        # # Remove x-axis ticks
        # ax.set_xticks([])

        # Create a table of h values
        df["Cooperativity"] = df["Cooperativity"].replace({"None": "-"})
        df["Cooperativity"] = df["Cooperativity"].replace({"NFkB": "N"})
        df["Cooperativity"] = df["Cooperativity"].replace({"IRF": "I"})

        # df["Cooperativity"] = df["Cooperativity"].replace({"NFkB": r"NF$\kappa$B"})

        table_data = df[sort_order[::-1]].drop_duplicates().values.tolist()
        # table_data = df[[r"$h_I$", r"$h_N$", "Cooperativity"]].drop_duplicates().values.tolist()

        # print(table_data)
        table_data = np.array(table_data).T
        table = plt.table(cellText=table_data, 
                          cellLoc='center', 
                          loc='bottom', 
                          rowLabels=sort_order[::-1], 
                          bbox=[0, -0.6, 1, 0.5])

        for key, cell in table.get_celld().items():
            cell.set_linewidth(0.5)

        # # Loop through the cells and change their color based on their text
        # colors = sns.color_palette("rocket", n_colors=4)
        # alpha = 0.5
        # colors = [(color[0], color[1], color[2], alpha) for color in colors]
        # for i in range(len(table_data)):
        #     for j in range(len(table_data[i])):
        #         cell = table[i, j]
        #         if table_data[i][j] in [5,"5","N"]:
        #             cell.set_facecolor(colors[0])
        #         elif table_data[i][j] in [3,"3",""]:
        #             cell.set_facecolor(colors[1])
        #         elif table_data[i][j] in [1,"1"]:
        #             cell.set_facecolor(colors[2])
        #         elif table_data[i][j] == "I":
        #             cell.set_facecolor(colors[3])

        # Adjust layout to make room for the table:
        plt.subplots_adjust(left=0.2, bottom=0.6)
        sns.despine()
        plt.xticks(rotation=90)
        plt.tight_layout()

        plt.savefig("%s/max_resid_%s.png" % (figures_dir, name), bbox_inches="tight")
        plt.close()

def make_supplemental_plots():
    figures_dir = "two_site_final_figures"
    os.makedirs(figures_dir, exist_ok=True)
    model = "two_site"
    training_data = pd.read_csv("../data/training_data.csv")
    beta = training_data["IFNb"]
    conditions = training_data["Stimulus"] + "_" + training_data["Genotype"]
    h_values = np.meshgrid([1,3], [1,3], [1,3])
    h_values = np.array(h_values).T.reshape(-1,3)

    results_dir = "parameter_scan/"

    # Plot max residual for each model
    hi, hn = np.meshgrid(np.arange(1,5), np.arange(1,5))
    models = ["h_%d_%d" % (hi.ravel()[i], hn.ravel()[i]) for i in range(len(hi.ravel()))]
    c_scan_models = ["h_%d_%d_c_scan" % (hi.ravel()[i], hn.ravel()[i]) for i in range(len(hi.ravel()))]
    models += c_scan_models
    print(models)
    max_residuals_df = pd.DataFrame()
    for m in models:
        fname = "%s/%s_best_fits_ifnb_predicted.csv" % ("%s/results_%s" % (results_dir, m), model)
        if not os.path.exists(fname):
            print("File %s does not exist, skipping" % fname)
            continue
        predictions = np.loadtxt(fname, delimiter=",")
        df = get_max_residual(predictions, beta, conditions)
        # print(df)
        df[r"$h_I$"] = m.split("_")[1]
        df[r"$h_N$"] = m.split("_")[2]
        df["Cooperativity"] = "+" if len(m.split("_")) > 4 else "None"
        df["model"] = m
        # df["model"] = r"$h_{I_1}=$%s, $h_{I_2}=$%s, $h_{N}=$%s" % (df[r"h_{I_1}"].values[0], df[r"h_{I_2}"].values[0], df[r"h_{N}"].values[0])
        max_residuals_df = pd.concat([max_residuals_df, df], ignore_index=True)

    print(max_residuals_df)

    plot_max_resid(max_residuals_df, figures_dir, "all_hill_and_coop_models")

    # Load best parameters with c-scan
    best_20_pars_df_1_1 = pd.read_csv("%s/results_h_1_1_c_scan/%s_best_fits_pars.csv" % (results_dir, model))
    best_20_pars_df_2_1 = pd.read_csv("%s/results_h_2_1_c_scan/%s_best_fits_pars.csv" % (results_dir, model))
    best_20_pars_df_3_1 = pd.read_csv("%s/results_h_3_1_c_scan/%s_best_fits_pars.csv" % (results_dir, model))
    best_20_pars_df_4_1 = pd.read_csv("%s/results_h_4_1_c_scan/%s_best_fits_pars.csv" % (results_dir, model))
    plot_parameters_one_plot(best_20_pars_df_1_1, "1", best_20_pars_df_2_1, "2", best_20_pars_df_3_1, "3", best_20_pars_df_4_1, "4", "best_20_pars_c_scan", figures_dir)

    # Calculate ifnb predictions with c-scan
    predictions_1_1 = np.loadtxt("%s/results_h_1_1_c_scan/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    predictions_2_1 = np.loadtxt("%s/results_h_2_1_c_scan/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    predictions_3_1 = np.loadtxt("%s/results_h_3_1_c_scan/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    predictions_4_1 = np.loadtxt("%s/results_h_4_1_c_scan/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    plot_predictions_one_plot(predictions_1_1, "1", predictions_2_1, "2", predictions_3_1, "3", predictions_4_1, "4", beta, conditions, 
                              "best_20_predictions_c_scan", figures_dir)
    
    # Load best parameters with c-scan (I&N hills)
    best_20_pars_df_1_3 = pd.read_csv("%s/results_h_1_3_c_scan/%s_best_fits_pars.csv" % (results_dir, model))
    best_20_pars_df_3_3 = pd.read_csv("%s/results_h_3_3_c_scan/%s_best_fits_pars.csv" % (results_dir, model))
    plot_parameters_one_plot(best_20_pars_df_1_1, "1", best_20_pars_df_1_3, "1", best_20_pars_df_3_1, "3", best_20_pars_df_3_3, "3", 
                             "best_20_pars_c_scan_I_N_hill", figures_dir, [1,3,1,3])


    # Calculate predictions with c-scan (I&N hills)
    predictions_1_1 = np.loadtxt("%s/results_h_1_1_c_scan/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    predictions_1_3 = np.loadtxt("%s/results_h_1_3_c_scan/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    predictions_3_1 = np.loadtxt("%s/results_h_3_1_c_scan/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    predictions_3_3 = np.loadtxt("%s/results_h_3_3_c_scan/%s_best_fits_ifnb_predicted.csv" % (results_dir, model), delimiter=",")
    plot_predictions_one_plot(predictions_1_1, "1", predictions_1_3, "1", predictions_3_1, "3", predictions_3_3, "3", beta, conditions, 
                              "best_20_predictions_c_scan_I_N_hill", figures_dir, [1,3,1,3])


    # Load best parameters with NFkB scan
    best_20_pars_df_1_1 = pd.read_csv("%s/results_h_1_1/%s_best_fits_pars.csv" % (results_dir, model))
    best_20_pars_df_1_3 = pd.read_csv("%s/results_h_1_3/%s_best_fits_pars.csv" % (results_dir, model))
    best_20_pars_df_3_1 = pd.read_csv("%s/results_h_3_1/%s_best_fits_pars.csv" % (results_dir, model))
    best_20_pars_df_3_3 = pd.read_csv("%s/results_h_3_3/%s_best_fits_pars.csv" % (results_dir, model))
    df_t_pars_1_1, df_k_pars_1_1, _, _ = make_parameters_data_frame(best_20_pars_df_1_1)
    df_t_pars_1_3, df_k_pars_1_3, _, _ = make_parameters_data_frame(best_20_pars_df_1_3)
    df_t_pars_3_1, df_k_pars_3_1, _, _ = make_parameters_data_frame(best_20_pars_df_3_1)
    df_t_pars_3_3, df_k_pars_3_3, num_t_pars, num_k_pars = make_parameters_data_frame(best_20_pars_df_3_3)
    df_all_t_pars = pd.concat([df_t_pars_1_1, df_t_pars_1_3, df_t_pars_3_1, df_t_pars_3_3], ignore_index=True)
    df_all_k_pars = pd.concat([df_k_pars_1_1, df_k_pars_1_3, df_k_pars_3_1, df_k_pars_3_3], ignore_index=True)
    df_all_t_pars[r"H_N"] = np.concatenate([np.repeat("1", len(df_t_pars_1_1)), np.repeat("3", len(df_t_pars_1_3)),
                                        np.repeat("1", len(df_t_pars_3_1)), np.repeat("3", len(df_t_pars_3_3))])
    df_all_t_pars[r"H_I"] = np.concatenate([np.repeat("1", len(df_t_pars_1_1)+len(df_t_pars_1_3)),
                                        np.repeat("3", len(df_t_pars_3_1)+len(df_t_pars_3_3))])
    df_all_k_pars[r"H_N"] = np.concatenate([np.repeat("1", len(df_k_pars_1_1)), np.repeat("3", len(df_k_pars_1_3)),
                                        np.repeat("1", len(df_k_pars_3_1)), np.repeat("3", len(df_k_pars_3_3))])
    df_all_k_pars[r"H_I"] = np.concatenate([np.repeat("1", len(df_k_pars_1_1)+len(df_k_pars_1_3)),
                                        np.repeat("3", len(df_k_pars_3_1)+len(df_k_pars_3_3))])
    df_all_t_pars["Model"] = r"$h_I=$" + df_all_t_pars[r"H_I"] + r", $h_N=$" + df_all_t_pars[r"H_N"]
    df_all_k_pars["Model"] = r"$h_I=$" + df_all_k_pars[r"H_I"] + r", $h_N=$" + df_all_k_pars[r"H_N"]
    make_pars_plots(num_t_pars, num_k_pars, df_all_t_pars, df_all_k_pars, "best_20_pars_NFkB_scan", figures_dir)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c","--contributions", action="store_true")
    parser.add_argument("-p","--param_scan", action="store_true")
    parser.add_argument("-s","--state_probs", action="store_true")
    parser.add_argument("-x","--supplemental", action="store_true")
    args = parser.parse_args()

    t = time.time()
    if args.contributions:
        # make_contribution_plots()
        raise NotImplementedError("Contribution plots not implemented yet")

    if args.param_scan:
        make_param_scan_plots()

    if args.state_probs:
        # make_state_probabilities_plots()
        raise NotImplementedError("State probabilities plots not implemented yet")
    
    if args.supplemental:
        make_supplemental_plots()


    print("Finished making all plots, took %.2f seconds" % (time.time() - t))

if __name__ == "__main__":
    main()
