import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
import copy
from datetime import datetime, timezone

from interactive_poster_backend.services import poster_service
from interactive_poster_backend.schemas import models as schemas
from interactive_poster_backend.database import models_db

@pytest.fixture
def mock_db_session():
    """Provides a mock SQLAlchemy session."""
    return MagicMock(spec=Session)

@pytest.fixture
def mock_chat_agent():
    """Provides a mock ChatAgent."""
    with patch('interactive_poster_backend.services.poster_service.ChatAgent') as mock:
        yield mock

@pytest.fixture
def base_poster_data():
    """Provides a base DbPoster object for tests."""
    return models_db.DbPoster(
        poster_id="test_poster_01",
        title="Initial Title",
        abstract="Initial Abstract",
        conclusion=None,
        theme="default_theme",
        selected_theme="default",
        last_modified=datetime.now(timezone.utc),
        pptx_file_path=None,
        preview_image_path=None,
        style_overrides=None,
        preview_status="completed",
        preview_last_error=None,
        sections=[]
    )

def test_process_poster_update_theme_change(mock_db_session, base_poster_data):
    """
    Tests that a simple theme update is processed correctly.
    """
    with patch('interactive_poster_backend.services.poster_service.crud.get_poster') as mock_get_poster, \
         patch('interactive_poster_backend.services.poster_service.crud.update_poster_data') as mock_update_poster:

        mock_get_poster.return_value = base_poster_data

        # ARRANGE: Create a deep copy for the return value to avoid modifying the input.
        updated_poster = copy.deepcopy(base_poster_data)
        updated_poster.selected_theme = "minimalist_dark"
        mock_update_poster.return_value = updated_poster

        request = schemas.OriginalLLMPromptRequest(selected_theme="minimalist_dark")

        # ACT
        result_poster, result_message = poster_service.process_poster_update(
            db=mock_db_session,
            poster_id="test_poster_01",
            request=request
        )

        # ASSERT
        mock_update_poster.assert_called_once()
        call_args = mock_update_poster.call_args[1]
        assert call_args['poster_update'].selected_theme == "minimalist_dark"

        assert result_poster.selected_theme == "minimalist_dark"
        assert "Theme updated to 'minimalist_dark'" in result_message

def test_process_poster_update_direct_content_update(mock_db_session, base_poster_data):
    """
    Tests a direct content update (e.g., editing the title) without involving the LLM.
    """
    with patch('interactive_poster_backend.services.poster_service.crud.get_poster') as mock_get_poster, \
         patch('interactive_poster_backend.services.poster_service.crud.update_poster_data') as mock_update_poster:

        mock_get_poster.return_value = base_poster_data

        # ARRANGE: Use a deep copy for the mock return value.
        updated_poster = copy.deepcopy(base_poster_data)
        updated_poster.title = "New Direct Title"
        mock_update_poster.return_value = updated_poster

        request = schemas.OriginalLLMPromptRequest(
            prompt_text="New Direct Title",
            target_element_id="poster_title",
            is_direct_update=True
        )

        # ACT
        result_poster, result_message = poster_service.process_poster_update(
            db=mock_db_session,
            poster_id="test_poster_01",
            request=request
        )

        # ASSERT
        mock_update_poster.assert_called_once()
        call_args = mock_update_poster.call_args[1]
        assert call_args['poster_update'].title == "New Direct Title"

        assert result_poster.title == "New Direct Title"
        assert "Content for 'poster_title' directly updated" in result_message

def test_process_poster_update_llm_update(mock_db_session, mock_chat_agent, base_poster_data):
    """
    Tests an LLM-based content update.
    """
    with patch('interactive_poster_backend.services.poster_service.crud.get_poster') as mock_get_poster, \
         patch('interactive_poster_backend.services.poster_service.crud.update_poster_data') as mock_update_poster:

        mock_get_poster.return_value = base_poster_data

        # ARRANGE: Mock the LLM response.
        mock_llm_response = MagicMock()
        mock_llm_response.msgs = [MagicMock(content="A Brand New Title from LLM")]
        mock_chat_agent.return_value.step.return_value = mock_llm_response

        # ARRANGE: Use a deep copy for the mock return value.
        updated_poster = copy.deepcopy(base_poster_data)
        updated_poster.title = "A Brand New Title from LLM"
        mock_update_poster.return_value = updated_poster

        request = schemas.OriginalLLMPromptRequest(
            prompt_text="make the title better",
            target_element_id="poster_title"
        )

        # ACT
        result_poster, result_message = poster_service.process_poster_update(
            db=mock_db_session,
            poster_id="test_poster_01",
            request=request
        )

        # ASSERT
        mock_chat_agent.return_value.step.assert_called_once()
        mock_update_poster.assert_called_once()

        update_call_args = mock_update_poster.call_args[1]
        assert update_call_args['poster_update'].title == "A Brand New Title from LLM"

        assert result_poster.title == "A Brand New Title from LLM"
        assert "LLM response" in result_message