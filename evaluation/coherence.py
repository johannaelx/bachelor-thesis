import os

from deepeval.metrics import ConversationalGEval
from deepeval.test_case import MultiTurnParams

from evaluation.pipeline import build_conversational_test_case

DEFAULT_JUDGE_MODEL = "gpt-4o"

COHERENCE_EVALUATION_STEPS = [
    "Read the full conversation in chronological order.",
    "Check whether later turns remain consistent with earlier ones (topics, facts, tone).",
    "Penalize clear contradictions or responses that ignore important prior context.",
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
