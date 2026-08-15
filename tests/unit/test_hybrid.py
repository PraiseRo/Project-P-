import pytest
import pytest_asyncio
from app.ai.hybrid_router import LocalIntentRouter
from app.tools.web_research import web_research

def test_local_intent_router():
    # Test local app open match
    res = LocalIntentRouter.match_local_command("open notepad")
    assert res is not None
    assert res[0] == "open_application"
    assert res[1] == {"application_name": "notepad"}

    # Test local system metrics match
    res_cpu = LocalIntentRouter.match_local_command("what is my cpu usage?")
    assert res_cpu is not None
    assert res_cpu[0] == "get_system_info"

    # Test web search match
    res_yt = LocalIntentRouter.match_local_command("search youtube for relaxing beats")
    assert res_yt is not None
    assert res_yt[0] == "search_web"
    assert res_yt[1]["engine"] == "youtube"

    # Non-local intent should return None to be handled by online LLM
    res_general = LocalIntentRouter.match_local_command("Tell me a funny joke about programming")
    assert res_general is None

@pytest.mark.asyncio
async def test_web_research_tool():
    res = await web_research("Python programming language")
    assert res["status"] in ["success", "warning"]
