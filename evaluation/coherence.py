import os

from deepeval.metrics import ConversationalGEval
from deepeval.test_case import MultiTurnParams

from evaluation.pipeline import build_conversational_test_case

DEFAULT_JUDGE_MODEL = "gpt-4o"

COHERENCE_EVALUATION_STEPS = [
    "1. Read the full conversation in chronological order.",
    "2. Identify the overarching goal or main topic of the conversation.",
    "3. Relational Check: Evaluate if consecutive turns form logical relations (e.g. causality, explanations) using context and world knowldge.",
    "4. Varify if each response provides at least a partial answer to the current implicit or explicit question.",
    "5. Penalize responses that read as isolated facts without a logical bridge to the prior turn.",
    "6. Penalize responses that derail from the overarching topic."
]


def create_coherence_metric() -> ConversationalGEval:
    model = os.getenv("EVAL_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)
    return ConversationalGEval(
        name="DialogCoherence",
        evaluation_steps=COHERENCE_EVALUATION_STEPS,
        evaluation_params=[MultiTurnParams.CONTENT],
        model=model,
    )


def evaluate_session_coherence(session, metric: ConversationalGEval) -> dict:
    test_case = build_conversational_test_case(session.messages)
    metric.measure(test_case)
    return {"score": metric.score, "reason": metric.reason}
