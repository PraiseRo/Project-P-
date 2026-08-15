import pytest
import pytest_asyncio
from app.core.routines import RoutineManager

@pytest.mark.asyncio
async def test_routine_manager():
    rm = RoutineManager()
    assert len(rm.routines) > 0
    
    # Test routine matching
    match1 = rm.match_routine("setup my workspace")
    assert match1 is not None
    assert len(match1["actions"]) >= 2

    match2 = rm.match_routine("hey please set up my workspace")
    assert match2 is not None

    match3 = rm.match_routine("study mode")
    assert match3 is not None
