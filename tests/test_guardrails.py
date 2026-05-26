import pytest
from app.agent.guardrails import classify, GuardrailResult
from tests.conftest import MockLLMAdapter, SequentialMockLLMAdapter


# ---------- helpers ----------

def make_llm(response: str) -> MockLLMAdapter:
    return MockLLMAdapter(response=response)


# ---------- category routing ----------

@pytest.mark.asyncio
@pytest.mark.parametrize("llm_word,expected_category,expected_block", [
    ("WELLNESS",  "WELLNESS", False),
    ("MEDICAL",   "MEDICAL",  True),
    ("CRISIS",    "CRISIS",   True),
    ("OTHER",     "OTHER",    True),
])
async def test_category_routing(llm_word, expected_category, expected_block):
    result = await classify("any message", make_llm(llm_word))
    assert result.category == expected_category
    assert result.should_block == expected_block


# ---------- wellness passes through ----------

@pytest.mark.asyncio
async def test_wellness_has_no_response():
    result = await classify("how much water should I drink?", make_llm("WELLNESS"))
    assert result.should_block is False
    assert result.response is None


# ---------- blocked categories have pre-written responses ----------

@pytest.mark.asyncio
async def test_crisis_response_contains_hotline():
    result = await classify("I want to hurt myself", make_llm("CRISIS"))
    assert result.should_block is True
    assert "988" in result.response
    assert "741741" in result.response


@pytest.mark.asyncio
async def test_medical_response_redirects_to_provider():
    result = await classify("do I have diabetes?", make_llm("MEDICAL"))
    assert result.should_block is True
    assert "healthcare provider" in result.response.lower()


@pytest.mark.asyncio
async def test_other_response_mentions_wellness_topics():
    # classify() makes two LLM calls for OTHER: one to categorise, one for the
    # dynamic redirect response. Use SequentialMockLLMAdapter so the second
    # call returns a realistic wellness-redirect string.
    llm = SequentialMockLLMAdapter([
        "OTHER",
        "That's outside my area, but I specialise in wellness topics like nutrition, sleep, and exercise — happy to help there!",
    ])
    result = await classify("what stocks should I buy?", llm)
    assert result.should_block is True
    assert "wellness" in result.response.lower()


# ---------- robustness: LLM goes off-script ----------

@pytest.mark.asyncio
@pytest.mark.parametrize("bad_output,expected_category", [
    ("wellness.",     "WELLNESS"),   # lowercase + punctuation
    ("WELLNESS now",  "WELLNESS"),   # extra words → take first token
    ("UNKNOWN_WORD",  "WELLNESS"),   # unknown → safe default
    ("",              "OTHER"),      # empty → OTHER
])
async def test_malformed_llm_output(bad_output, expected_category):
    result = await classify("some message", make_llm(bad_output))
    assert result.category == expected_category
