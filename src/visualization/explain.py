import click
from src.visualization.explainer.html_components import build_header
import src.visualization.visualize as viz
from mlflow.tracking import MlflowClient
from datetime import datetime
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import locale
import numpy as np
import copy
import json
from pathlib import Path
import pandas as pd
from scipy import stats

import pyarrow.parquet as pq
import os

## added mm ##
import torch
#if torch.cuda.current_device() > 0:
#    map_location=torch.cuda.device(0)
#if not torch.cuda.is_available():
#    map_location=torch.cuda.device('cpu')
##############

locale.setlocale(locale.LC_ALL, '')

git_repo = "https://github.com/yvesmauron/time-series-anomaly-detection/tree"
mlflow_tracking_server = "http://127.0.0.1:5000/#/experiments"

external_stylesheets = ['assets/style_2.css', 'assets/style.css']

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
)

mlflow_client = MlflowClient()
experiments = mlflow_client.get_experiment_by_name("SMAVRA")
runs = mlflow_client.list_run_infos(experiments.experiment_id)

scored_runs = [
    os.path.basename(p) for p in Path("data/output/score").iterdir()
]
run_labels = [
    {
        "label": "Run from " +
        f"{datetime.utcfromtimestamp(r.start_time / 1000.0).strftime('%Y-%m-%d %H:%M:%S')}",
        "value": r.run_id
    } for r in runs
    if r.run_id in scored_runs
]

layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="Dash Data Visualization",
    # dragmode="select",
    showlegend=False
)

app.scripts.config.serve_locally = True
########################################
# Cionnect to adls and list available files

app.layout = html.Div(
    [
        html.Div(id='hdiv_epoch_mu', style={"display": "none"}),
        html.Div(id='hdiv_epoch_std', style={"display": "none"}),
        html.Div(id='hdiv_maskpres_mu', style={"display": "none"}),
        html.Div(id='hdiv_maskpres_std', style={"display": "none"}),
        html.Div(id='hdiv_delivol_mu', style={"display": "none"}),
        html.Div(id='hdiv_delivol_std', style={"display": "none"}),
        html.Div(id='hdiv_respflow_mu', style={"display": "none"}),
        html.Div(id='hdiv_respflow_std', style={"display": "none"}),
        build_header(app),
        html.Div(
            [
                html.Div(
                    [
                        html.H6(
                            'Filter by run start date:',
                            className="control_label"
                        ),
                        dcc.Dropdown(
                            id="dd_runs",
                            options=run_labels,
                            multi=False,
                            value=run_labels[0]["value"],
                            className="dcc_control",
                        )
                    ],
                    className="pretty_container four columns",
                    id="cross-filter-options",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Link(
                                    children=html.H6(id="tile_run_id"),
                                    id="link_mlflow",
                                    href=""
                                ),
                                html.P("Run Id")
                            ],
                            id="run_id",
                            className="mini_container two columns",
                        ),
                        html.Div(
                            [
                                dcc.Link(
                                    children=html.H6(id="tile_git_commit"),
                                    id="link_github",
                                    href=""
                                ),
                                html.P("Git")
                            ],
                            id="git_commit",
                            className="mini_container two columns",
                        ),
                        html.Div(
                            [
                                html.H6(id="tile_n_epochs"),
                                html.P("Nr Epoch")
                            ],
                            id="n_epoch",
                            className="mini_container two columns",
                        ),
                        html.Div(
                            [
                                html.H6(id="tile_recon_loss"),
                                html.P("Recon Loss")
                            ],
                            id="recon_loss",
                            className="mini_container two columns",
                        ),
                        html.Div(
                            [
                                html.H6(id="tile_kld_latent"),
                                html.P("KLD Latent")
                            ],
                            id="kld_latent",
                            className="mini_container two columns",
                        ),
                        html.Div(
                            [
                                html.H6(id="tile_kld_attention"),
                                html.P("KLD Attention")
                            ],
                            id="kld_attention",
                            className="mini_container two columns",
                        )
                    ],
                    className="eight columns",
                    id="info-measures",
                    style={"display": "flex", "flex-direction": "row"}
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div([
                    html.Div(
                        html.Div(
                            [dcc.Graph(id="g_latent_size")],
                            className="pretty_container"
                        ),
                        className="four columns",
                        style={"margin-left": "0px"}
                    ),
                    html.Div(
                        html.Div(
                            [dcc.Graph(id="g_attention_1")],
                            className="pretty_container"
                        ),
                        className="four columns",
                        style={"margin-left": "0px"}
                    ),
                    html.Div(
                        html.Div(
                            [dcc.Graph(id="g_attention_2")],
                            className="pretty_container"
                        ),
                        className="four columns"
                    ),
                ],
                    className="twelve columns",
                    id="latent-attention",
                    style={"display": "flex", "flex-direction": "row"}
                )
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H6(id="tile_anomaly_z"),
                                html.P("Anomaly Z")
                            ],
                            id="anomaly_z",
                            className="mini_container twelve columns",
                            style={"margin-left": "0px"}
                        ),
                        # html.Div(
                        #     [
                        #         html.H6(id="tile_anomaly_osvn"),
                        #         html.P("Anomaly OSVM")
                        #     ],
                        #     id="anomaly_osvn",
                        #     className="mini_container twelve columns",
                        #     style={"margin-left": "0px"}
                        # ),
                        html.Div(
                            [
                                html.H6(id="tile_epoch_mse"),
                                html.P("Epoch MSE")
                            ],
                            id="epoch_mse",
                            className="mini_container twelve columns",
                            style={"margin-left": "0px"}
                        ),
                        html.Div(
                            [
                                html.H6(id="tile_epoch_mse_z"),
                                html.P("Epoch MSE Z")
                            ],
                            id="epoch_mse_z",
                            className="mini_container twelve columns",
                            style={"margin-left": "0px"}
                        ),
                        html.Div(
                            [
                                html.H6(id="tile_maskpres_z"),
                                html.P("MaskPres Z")
                            ],
                            id="maskpres_z",
                            className="mini_container twelve columns",
                            style={"margin-left": "0px"}
                        ),
                        html.Div(
                            [
                                html.H6(id="tile_delivol_z"),
                                html.P("DeliVol Z")
                            ],
                            id="delivol_z",
                            className="mini_container twelve columns",
                            style={"margin-left": "0px"}
                        ),
                        html.Div(
                            [
                                html.H6(id="tile_respflow_z"),
                                html.P("Respflow Z")
                            ],
                            id="respflow_z",
                            className="mini_container twelve columns",
                            style={"margin-left": "0px"}
                        ),
                    ],
                    className="two columns",
                    style={
                        "display": "flex",
                        "flex-direction": "column",
                        "margin-left": "0px"}
                ),
                html.Div([
                    html.Div(
                        [dcc.Graph(id="g_reconstruction")],
                        className="pretty_container"
                    )
                ],
                    className="ten columns"
                )
            ],
            className="column flex-display",
        ),
        html.Div(
            [
                html.Div(
                    html.Div(
                        [dcc.Markdown("""
                                **Click Data**

                                Click on points in the graph.
                            """),
                            html.Pre(id='click-data'), ],
                        className="pretty_container",
                    ),
                    className="twelve columns"
                )
            ],
            className="row flex-display",
        )
    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"}
)


@ app.callback(
    [
        # Output("tile_kld_latent_weight", "children"),
        # Output("tile_kld_attention_weight", "children"),
        Output("tile_run_id", "children"),
        Output("link_mlflow", "href"),
        Output("tile_git_commit", "children"),
        Output("link_github", "href"),
        Output("tile_n_epochs", "children"),
        Output("tile_recon_loss", "children"),
        Output("tile_kld_latent", "children"),
        Output("tile_kld_attention", "children")
    ],
    [
        Input("dd_runs", "value")
    ]
)
def update_tiles(run_id):
    mlflow_client = MlflowClient()
    # get run to be explained
    run_data = mlflow_client.get_run(run_id).data

    tags = run_data.tags
    params = run_data.params
    metrics = run_data.metrics
    exp = mlflow_client.get_experiment_by_name("SMAVRA")

    return(
        [

            # params['kld_latent_loss_weight'],
            # params['kld_attention_loss_weight'],
            run_id[:6],
            f"{mlflow_tracking_server}/{exp.experiment_id}/runs/{run_id}",
            tags['mlflow.source.git.commit'][:6],
            f"{git_repo}/{tags['mlflow.source.git.commit']}",
            params['n_epochs'],
            f"{round(metrics['Reconstruction Loss'], 2):n}",
            f"{round(metrics['KLD-Latent Loss'], 2):n}",
            f"{round(metrics['KLD-Attention Loss'], 2):n}"
        ]
    )


@ app.callback(
    [
        Output("hdiv_epoch_mu", "children"),
        Output("hdiv_epoch_std", "children"),
        Output("hdiv_maskpres_mu", "children"),
        Output("hdiv_maskpres_std", "children"),
        Output("hdiv_delivol_mu", "children"),
        Output("hdiv_delivol_std", "children"),
        Output("hdiv_respflow_mu", "children"),
        Output("hdiv_respflow_std", "children")
    ],
    [
        Input("dd_runs", "value")
    ]
)
def update_run_stats(run_id):

    score_dir = os.path.join("data/output/score/", run_id)
    score = []
    for p in Path(score_dir).iterdir():
        df = pq.read_table(
            p,
            columns=[
                "epoch_id",
                "epoch_mse",
                "mask_press_se",
                "resp_flow_se",
                "delivered_volum_se"
            ]).to_pandas()
        df = df \
            .groupby("epoch_id") \
            .agg(
                {
                    "epoch_mse": "mean",
                    "mask_press_se": "mean",
                    "resp_flow_se": "mean",
                    "delivered_volum_se": "mean"
                }).reset_index()
        score.append(df.iloc[:, 1:])
    df = pd.concat(score, axis=0)

    means = []
    stds = []
    for c in df.columns:
        col_val = df[c].values
        p = np.percentile(col_val, 95)
        upper_limit = np.median(col_val) + (3 * p)
        mu = stats.tmean(col_val, limits=[0, upper_limit])
        sd = stats.tstd(col_val, limits=[0, upper_limit])

        means.append(mu)
        stds.append(sd)

    return means + stds


@ app.callback(
    Output("g_latent_size", "figure"),
    [
        Input("dd_runs", "value")
    ]
)
def update_latent(run_id):

    # just for demo purposes -- delete afterwards

    # - diskonnektion

    layout_plot = copy.deepcopy(layout)

    df, pca_data, explained, labels, probs = viz.latent_pca_data(
        run_id=run_id, pca_components=2)

    df["symbol"] = "circle"
    df.loc[(df.epoch > 481) & (df.file_name ==
                               "20201214_120001"), "symbol"] = "diamond"
    # if demo:
    #     opacity = 0.1 + \
    #         (((df.epoch > 481) & (df.file_name == "20201214_120001")) * 0.9)

    # print(opacity.loc[labels == -1])
    data = [
        dict(
            type="scatter",
            mode="markers",
            name=str(label),
            x=pca_data.loc[labels == label, "PC1"].values,
            y=pca_data.loc[labels == label, "PC2"].values,
            text=(
                "File: " +
                df.loc[labels == label, "file_name"] +
                "<br> Epoch:" +
                df.loc[labels == label, "epoch"].astype(str)).values +
            "<br> Class:" + str(label),
            hovertemplate="<b>%{text}</b><br>"
            "<br><b>PC1:</b>: %{x}" +
            "<br><b>PC2:</b>: %{y}",
            marker=dict(
                # color=np.log(df.epoch_loss.astype("float")),-
                color=str(label),
                # coloraxis='coloraxis',
                colorbar=dict(),
                showscale=False,
                symbol=df.symbol.loc[labels == label]
                # opacity=opacity.loc[labels == label]
                # colorscale="Viridis"
            ),

            customdata=df.loc[labels == label, [
                "epoch", "file_name"]].values.reshape(-1, 2)
        )
        for label in np.unique(labels)
    ]

    layout_plot["title"] = f'PCA Latent; Explained Variance: {explained:.2f}%'
    layout_plot['clickmode'] = 'event+select'
    layout_plot['showlegend'] = True

    figure = dict(data=data, layout=layout_plot)

    return figure


@ app.callback(
    Output('click-data', 'children'),
    [Input('g_latent_size', 'clickData')])
def display_click_data(clickData):
    return json.dumps(clickData, indent=2)


@ app.callback(
    [
        Output('g_attention_1', 'figure'),
        Output('g_attention_2', 'figure')
    ],
    [
        Input('g_latent_size', 'clickData'),
        State('dd_runs', 'value')
    ])
def update_attention(clickData, run_id):
    epoch, file_name = clickData["points"][0]["customdata"]

    attention = viz.epoch_attention(
        run_id=run_id, session=file_name, epoch_nr=epoch
    )
    figs = []
    for i in range(len(attention)):
        data = dict(
            type="heatmap",
            name="PCA Latent",
            z=attention[i]
        )
        layout_plot = copy.deepcopy(layout)
        layout_plot["title"] = f'Attention {i}; Epoch: {int(epoch)}'

        figure = dict(data=[data], layout=layout_plot)

        figs.append(figure)

    if len(figs) == 1:
        figs.append(None)
    # import plotly.express as px
    # fig = px.imshow(attention[0])

    return figs


@ app.callback(
    [
        Output('g_reconstruction', 'figure'),
        Output('tile_anomaly_z', 'children'),
        Output('tile_epoch_mse', 'children'),
        Output('tile_epoch_mse_z', 'children'),
        Output('tile_maskpres_z', 'children'),
        Output('tile_delivol_z', 'children'),
        Output('tile_respflow_z', 'children')
    ],
    [
        Input('g_latent_size', 'clickData'),
        State('dd_runs', 'value'),
        State("hdiv_epoch_mu", "children"),
        State("hdiv_epoch_std", "children"),
        State("hdiv_maskpres_mu", "children"),
        State("hdiv_maskpres_std", "children"),
        State("hdiv_delivol_mu", "children"),
        State("hdiv_delivol_std", "children"),
        State("hdiv_respflow_mu", "children"),
        State("hdiv_respflow_std", "children")
    ])
def update_reconstruction(
    clickData,
    run_id,
    epoch_mu,
    epoch_std,
    maskpres_mu,
    maskpres_std,
    delivol_mu,
    delivol_std,
    respflow_mu,
    respflow_std
):
    # get click data
    epoch, file_name = clickData["points"][0]["customdata"]

    # get dataframe
    scored_path = Path(os.path.join("data", "output", "score", run_id))
    df = pq.read_table(
        os.path.join(scored_path, f"{file_name}_0_HRD.edf.parquet")
    ).to_pandas()
    df = df.loc[df["epoch_id"] == epoch, :]

    # get z values
    epoch_mse = df["epoch_mse"].values[0]
    mask_pres = np.mean(df["mask_press_se"].values)
    resp_flow = np.mean(df["resp_flow_se"].values)
    deli_vol = np.mean(df["delivered_volum_se"].values)

    epoch_mse_z = (epoch_mse - epoch_mu) / epoch_std
    mask_pres_z = (mask_pres - maskpres_mu) / maskpres_std
    deli_vol_z = (deli_vol - delivol_mu) / delivol_std
    resp_flow_z = (resp_flow - respflow_mu) / respflow_std

    anomaly = (
        ">97.5% P"
        if mask_pres_z > 3 or deli_vol_z > 3 or resp_flow_z > 3
        else "<97.6 P"
    )

    # get figure
    figure = viz.plot_signals(file_name, df)

    figure.update_layout(
        plot_bgcolor="#F9F9F9",
        paper_bgcolor="#F9F9F9",
        height=800
    )

    return(
        figure,
        anomaly,
        round(epoch_mse, 2),
        round(epoch_mse_z, 2),
        round(mask_pres_z, 2),
        round(deli_vol_z, 2),
        round(resp_flow_z, 2)
    )


if __name__ == '__main__':
    app.run_server(debug=False)
# server = app.server
