from loguru import logger
import plotly.graph_objects as go


def generate_report(leitnerobject) -> None:
    logger.info(f"Generating report for user: {leitnerobject.username}")

    stages = [
        "Leitner Stage 1",
        "Leitner Stage 2",
        "Leitner Stage 3",
        "Leitner Stage 4",
    ]
    stage_texts = [[], [], [], []]
    stage_colors = [[], [], [], []]

    for phrase in leitnerobject.active_phrases:
        stage_index = phrase.leitner_stage - 1
        stage_texts[stage_index].append(phrase.text)
        if phrase.mistakes > 0:
            stage_colors[stage_index].append("firebrick")
        elif phrase.correct_answers > 0:
            stage_colors[stage_index].append("navy")
        else:
            stage_colors[stage_index].append("black")

    stages_with_counts = [
        f"{stage} [{len(stage_texts[i])} items]" for i, stage in enumerate(stages)
    ]

    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=stages_with_counts,
                    fill_color="midnightblue",
                    align="left",
                    font=dict(color="white"),
                ),
                cells=dict(
                    values=stage_texts,
                    fill_color="whitesmoke",
                    align="left",
                    font=dict(color=stage_colors),
                ),
            )
        ]
    )

    fig.update_layout(
        title=f"Phrases You're Currently Learning: {leitnerobject.username}"
    )

    image_path = f"data/{leitnerobject.username}_report.png"
    fig.write_image(image_path, width=1200, height=800, scale=2)

    return image_path
