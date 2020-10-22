import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pyarrow.parquet as pq
import shutil
from pathlib import Path
import os
import logging

log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)

report_figures_path = Path("reports/figures")
scored_path = Path("data/output/score")
if report_figures_path.exists():
    shutil.rmtree(report_figures_path)

color_palette = {
    "resp_flow": "rgba(247, 201, 77, 1)",
    "deli_volu": "rgba(64, 145, 182, 1)",
    "mask_pres": "rgba(105, 173, 82, 1)",
    "true": "rgba(0, 0, 0, 1)",
    "se_resp_flow": "rgba(247, 201, 77, 1)",
    "se_deli_volu": "rgba(64, 145, 182, 1)",
    "se_mask_pres": "rgba(105, 173, 82, 1)",
}

report_figures_path.mkdir()

sessions = [str(os.path.basename(p))[:15] for p in scored_path.iterdir()]

# sessions = sessions[-1:]

for session in sessions:

    logging.info(f"Report session: {session}")

    df = pq.read_table(
        f"data/output/score/{session}_0_HRD.edf.parquet").to_pandas()
    df = df.loc[df["delivered_volum"] > -32768, :]

    # subplot -----
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=("Resp Flow", "Delivered Volume",
                        "Mask Pressure", "Anomaly Score")
    )

    # error -----
    fig.add_trace(
        go.Scatter(
            x=df.timestamp,
            y=df.mask_press_se,
            mode='lines',
            name='Scaled SE MaskPressure',
            line=dict(
                color=color_palette["se_mask_pres"]
            )
        ),
        row=4,
        col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df.timestamp,
            y=df.delivered_volum_se,
            mode='lines',
            name='Scaled SE Deliveredvolume',
            line=dict(
                color=color_palette["se_deli_volu"]
            )
        ),
        row=4,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.timestamp,
            y=df.resp_flow_se,
            mode='lines',
            name='Scaled SE RespFlow',
            line=dict(
                color=color_palette["se_resp_flow"]
            )
        ),
        row=4,
        col=1
    )

    # Mask Pressure -----
    fig.add_trace(
        go.Scatter(
            x=df.timestamp,
            y=df.mask_press,
            mode='lines',
            name='Mask Pressure (True)',
            line=dict(
                color=color_palette["true"]
            )
        ),
        row=3,
        col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df.timestamp,
            y=df.mask_press_mu,
            mode='lines',
            name='Mask Pressure (Predicted)',
            line=dict(
                color=color_palette["mask_pres"]
            )
        ),
        row=3,
        col=1
    )

    # Delivered Volume -----
    fig.add_trace(
        go.Scatter(
            x=df.timestamp,
            y=df.delivered_volum,
            mode='lines',
            name='Delivered Volume (True)',
            line=dict(
                color=color_palette["true"]
            )
        ),
        row=2,
        col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df.timestamp,
            y=df.delivered_volum_mu,
            mode='lines',
            name='Delivered Volume (Predicted)',
            line=dict(
                color=color_palette["deli_volu"]
            )
        ),
        row=2,
        col=1
    )

    # Respiration Flow -----
    fig.add_trace(
        go.Scatter(
            x=df.timestamp,
            y=df.resp_flow,
            mode='lines',
            name='Resp Flow (True)',
            line=dict(
                color=color_palette["true"]
            )
        ),
        row=1,
        col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df.timestamp,
            y=df.resp_flow_mu,
            mode='lines',
            name='Resp Flow (Predicted)',
            line=dict(
                color=color_palette["resp_flow"]
            )
        ),
        row=1,
        col=1
    )

    fig.update_layout(
        title_text=f"Session example: {session}",
        legend_title="Legend Title",
        font=dict(
            family="Courier New, monospace",
            size=18
        )
    )

    fig.write_html(f"reports/figures/{session}.html")