import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from eda_tools.probability_distribution import ProbabilityDistribution
from eda_tools.statistical_tools import clip_outliers, DiscretizationMagnitude, discretize_variable, \
    estimate_probability_density_function

def histogram(
        df,
        feature,
        binary_target,
        clip_outliers_max_deviation=None,
        number_of_bins=8,
        keep_group_size_constant=False
):
    def get_interval_properties(intervals):
        midpoints = intervals.map(lambda interval: interval.mid)
        widths = intervals.map(lambda interval: interval.length).astype(float)
        return midpoints, widths

    distribution = ProbabilityDistribution.from_variables_samples(df)

    if clip_outliers_max_deviation is not None:
        distribution.apply_function_to_variable(feature, lambda s: clip_outliers(s, clip_outliers_max_deviation))

    discretization_magnitude = DiscretizationMagnitude.QUANTILE if keep_group_size_constant else DiscretizationMagnitude.VALUE
    discretize_function = lambda s: discretize_variable(s, number_of_bins, discretization_magnitude)
    distribution.apply_function_to_variable(feature, discretize_function)

    distribution_of_interest = distribution.select_variables([feature, binary_target])
    freq = distribution_of_interest.select_variables(feature).get_distribution()
    positive_rate = distribution_of_interest.conditioned_on(feature).given({binary_target: True}).get_distribution()

    midpoints, widths = get_interval_properties(freq.index)
    probability_density = freq / freq.sum() / widths

    return go.Figure(
        data=[
            go.Bar(x=midpoints, y=probability_density, width=widths, yaxis="y", showlegend=False, text=freq),
            go.Scatter(x=midpoints, y=positive_rate, yaxis="y2", showlegend=False, hovertemplate="%{y:.1%}"),
        ],
        layout=go.Layout(
            xaxis_title=feature,
            yaxis=dict(
                title=f"{feature} probability density",
                titlefont=dict(
                    color=px.colors.qualitative.Plotly[0]
                ),
                side="left",
                tickfont_color=px.colors.qualitative.Plotly[0]
            ),
            yaxis2=dict(
                title=f"{binary_target} positive rate",
                range=[0, positive_rate.max() * 1.05],
                anchor="x",
                overlaying="y",
                side="right",
                titlefont=dict(
                    color=px.colors.qualitative.Plotly[1]
                ),
                tickfont_color=px.colors.qualitative.Plotly[1],
                tickmode="sync",
                tickformat = '.0%'
            ),
        )
    )


def probability_density_function(
        df,
        feature,
        binary_target,
        bandwidth=1
):
    feature_series = df[feature]
    binary_target_series = df[binary_target]

    feature_vector = np.linspace(feature_series.min(), feature_series.max(), 100)
    feature_pdf = estimate_probability_density_function(feature_series, bandwidth)(feature_vector)

    feature_positive_target = feature_series[binary_target_series == True]
    feature_positive_target_pdf = estimate_probability_density_function(feature_positive_target, bandwidth)(
        feature_vector)

    overall_positive_rate = binary_target_series.mean()
    feature_positive_target_density = feature_positive_target_pdf * overall_positive_rate

    positive_rate = feature_positive_target_density / feature_pdf

    return go.Figure(
        data=[
            go.Scatter(x=feature_vector, y=feature_pdf, yaxis="y", showlegend=False),
            go.Scatter(x=feature_vector, y=positive_rate, yaxis="y2", showlegend=False)
        ],
        layout=go.Layout(
            xaxis_title=f"feature",
            yaxis=dict(
                title=f"{feature} PDF",
                titlefont=dict(
                    color=px.colors.qualitative.Plotly[0]
                ),
                side="left",
                tickfont_color=px.colors.qualitative.Plotly[0]
            ),
            yaxis2=dict(
                title="Success rate",
                range=[0, positive_rate.max() * 1.05],
                anchor="x",
                overlaying="y",
                side="right",
                titlefont=dict(
                    color=px.colors.qualitative.Plotly[1]
                ),
                tickfont_color=px.colors.qualitative.Plotly[1],
                tickmode="sync",
                tickformat='.0%'
            ),
        )
    )
