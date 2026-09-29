from typing_extensions import Annotated, TypedDict

from langchain.chat_models import init_chat_model

# LLM-as-judge instructions
grader_instructions = """You are a teacher grading a quiz.

You will be given a QUESTION, the GROUND TRUTH (correct) RESPONSE, and the STUDENT RESPONSE.

Here is the grade criteria to follow:
(1) Grade the student responses based ONLY on their factual accuracy relative to the ground truth answer.
(2) Ensure that the student response does not contain any conflicting statements.
(3) It is OK if the student response contains more information than the ground truth response, as long as it is factually accurate relative to the  ground truth response.

Correctness:
True means that the student's response meets all of the criteria.
False means that the student's response does not meet all of the criteria.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct."""


# LLM-as-judge output schema
class Grade(TypedDict):
    """Compare the expected and actual answers and grade the actual answer."""

    reasoning: Annotated[
        str,
        ...,
        "Explain your reasoning for whether the actual response is correct or not.",
    ]
    is_correct: Annotated[
        bool,
        ...,
        "True if the student response is mostly or exactly correct, otherwise False.",
    ]


# Judge LLM
grader_llm = init_chat_model(
    "gpt-5.4-mini", temperature=0
).with_structured_output(Grade, method="json_schema", strict=True)


# Evaluator function
async def final_answer_correct(
    inputs: dict, outputs: dict, reference_outputs: dict
) -> bool:
    """Evaluate if the final response is equivalent to reference response."""

    # Note that we assume the outputs has a 'response' dictionary. We'll need to make sure
    # that the target function we define includes this key.
    user = f"""QUESTION: {inputs['question']}
    GROUND TRUTH RESPONSE: {reference_outputs['response']}
    STUDENT RESPONSE: {outputs['response']}"""

    grade = await grader_llm.ainvoke(
        [
            {"role": "system", "content": grader_instructions},
            {"role": "user", "content": user},
        ]
    )
    return grade["is_correct"]


# Evaluator function for expected tools
def used_expected_tools(outputs: dict, reference_outputs: dict) -> bool:
    expected = reference_outputs["expected_tools"]
    actual = outputs["tools_called"]
    if not expected:
        return actual == []
    return all(t in actual for t in expected)


# LLM-as-judge instructions for conversation coherence
coherence_instructions = """You are a teacher grading how well a customer service \
agent held up its end of a multi-turn conversation.

You will be given the full CONVERSATION (a numbered list of the customer's turns, \
in order), a REFERENCE FINAL RESPONSE showing what a coherent agent should have \
said to the last turn, and the agent's actual STUDENT FINAL RESPONSE to that same \
last turn.

Here is the grade criteria to follow:
(1) Grade ONLY whether the student response correctly used context from the \
earlier turns of the conversation (e.g. resolving "it"/"that"/"the first one", \
staying on the original topic after a detour, remembering facts established \
earlier) to answer the final turn. This is not a test of exact wording -- it is \
a test of whether the agent tracked the conversation instead of treating the \
final turn as if it arrived with no history.
(2) It is OK if the student response contains more information than the \
reference response, or phrases things differently, as long as it correctly \
carries over the relevant context from earlier turns.
(3) If the student response ignores, contradicts, or fails to resolve context \
that the final turn depended on, it is not coherent, even if the response would \
otherwise be a reasonable standalone answer.

Coherence:
True means that the student's response meets all of the criteria.
False means that the student's response does not meet all of the criteria.

Explain your reasoning in a step-by-step manner to ensure your reasoning and conclusion are correct."""


# LLM-as-judge output schema for conversation coherence
class CoherenceGrade(TypedDict):
    """Compare the reference and actual final responses and grade conversational coherence."""

    reasoning: Annotated[
        str,
        ...,
        "Explain your reasoning for whether the actual response correctly used earlier conversation context.",
    ]
    is_coherent: Annotated[
        bool,
        ...,
        "True if the student response correctly used context from earlier turns, otherwise False.",
    ]


# Judge LLM for conversation coherence
coherence_llm = init_chat_model(
    "gpt-5.4-mini", temperature=0
).with_structured_output(CoherenceGrade, method="json_schema", strict=True)


# Evaluator function for conversation coherence
async def conversation_coherent(
    inputs: dict, outputs: dict, reference_outputs: dict
) -> bool:
    """Evaluate if the final response correctly used context from earlier turns."""

    conversation = "\n".join(
        f"{i + 1}. {turn}" for i, turn in enumerate(inputs["messages"])
    )
    user = f"""CONVERSATION:
    {conversation}

    REFERENCE FINAL RESPONSE: {reference_outputs['response']}
    STUDENT FINAL RESPONSE: {outputs['response']}"""

    grade = await coherence_llm.ainvoke(
        [
            {"role": "system", "content": coherence_instructions},
            {"role": "user", "content": user},
        ]
    )
    return grade["is_coherent"]


UNGRACEFUL_RED_FLAGS = [
    "Traceback",
    "Error:",
    "Exception",
    "psycopg2",
    "sqlalchemy",
    "Errno",
    "NoneType",
    "Unauthorized",
    "500 Internal Server Error",
    "stack trace",
]


# Evaluator function for graceful error handling
def is_graceful_response(outputs: dict) -> bool:
    response = outputs["response"]
    return not any(flag in response for flag in UNGRACEFUL_RED_FLAGS)
