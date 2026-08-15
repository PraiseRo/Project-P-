import pytest
import pytest_asyncio
from app.ai.hybrid_router import LocalIntentRouter, clean_spoken_input
from app.tools.apps import _discover_windows_app
from app.tools.web_research import web_research

def test_clean_spoken_input():
    assert clean_spoken_input("Hey P, please open the paint app") == "open the paint app"
    assert clean_spoken_input("Can you please check my cpu usage?") == "check my cpu usage"
    assert clean_spoken_input("Could you open notepad") == "open notepad"

def test_paint_app_discovery():
    assert _discover_windows_app("paint") == "mspaint.exe"
    assert _discover_windows_app("paint app") == "mspaint.exe"
    assert _discover_windows_app("mspaint") == "mspaint.exe"
    assert _discover_windows_app("calc") == "calc.exe"

def test_local_intent_router_with_conversational_speech():
    # "open paint app"
    res1 = LocalIntentRouter.match_local_command("open paint app")
    assert res1 is not None
    assert res1[0] == "open_application"
    assert res1[1] == {"application_name": "paint"}

    # "Please can you open the paint app"
    res2 = LocalIntentRouter.match_local_command("Please can you open the paint app")
    assert res2 is not None
    assert res2[0] == "open_application"
    assert res2[1] == {"application_name": "paint"}

    # "Hey P, take a screenshot"
    res3 = LocalIntentRouter.match_local_command("Hey P, take a screenshot")
    assert res3 is not None
    assert res3[0] == "take_screenshot"
