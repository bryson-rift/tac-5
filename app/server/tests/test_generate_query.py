import pytest
from unittest.mock import patch, MagicMock
from core.llm_processor import (
    generate_test_query,
    generate_test_query_with_openai,
    generate_test_query_with_anthropic
)


@pytest.fixture
def sample_schema():
    """Sample database schema for testing"""
    return {
        'tables': {
            'users': {
                'columns': {
                    'id': 'INTEGER',
                    'name': 'TEXT',
                    'email': 'TEXT',
                    'signup_date': 'TEXT'
                },
                'row_count': 20
            },
            'products': {
                'columns': {
                    'id': 'INTEGER',
                    'name': 'TEXT',
                    'price': 'REAL',
                    'category': 'TEXT'
                },
                'row_count': 32
            }
        }
    }


@pytest.fixture
def empty_schema():
    """Empty database schema for testing"""
    return {
        'tables': {}
    }


@pytest.fixture
def single_table_schema():
    """Single table database schema for testing"""
    return {
        'tables': {
            'employees': {
                'columns': {
                    'id': 'INTEGER',
                    'name': 'TEXT',
                    'department': 'TEXT',
                    'salary': 'REAL'
                },
                'row_count': 50
            }
        }
    }


class TestGenerateTestQueryWithOpenAI:
    """Tests for generate_test_query_with_openai function"""

    @patch('core.llm_processor.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_generate_test_query_success(self, mock_openai_class, sample_schema):
        """Test successful query generation with OpenAI"""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Show me all users who signed up in the last month."
        mock_client.chat.completions.create.return_value = mock_response

        # Call function
        result = generate_test_query_with_openai(sample_schema)

        # Assertions
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Show me all users" in result
        mock_client.chat.completions.create.assert_called_once()

    @patch('core.llm_processor.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_generate_test_query_removes_quotes(self, mock_openai_class, sample_schema):
        """Test that quotes are removed from generated queries"""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock response with quotes
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '"What are the top 5 most expensive products?"'
        mock_client.chat.completions.create.return_value = mock_response

        # Call function
        result = generate_test_query_with_openai(sample_schema)

        # Assertions
        assert not result.startswith('"')
        assert not result.endswith('"')
        assert result == "What are the top 5 most expensive products?"

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_test_query_no_api_key(self, sample_schema):
        """Test error handling when API key is missing"""
        with pytest.raises(Exception) as exc_info:
            generate_test_query_with_openai(sample_schema)

        assert "OPENAI_API_KEY" in str(exc_info.value)

    @patch('core.llm_processor.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_generate_test_query_api_error(self, mock_openai_class, sample_schema):
        """Test error handling when OpenAI API fails"""
        # Mock OpenAI client to raise error
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        # Call function and expect exception
        with pytest.raises(Exception) as exc_info:
            generate_test_query_with_openai(sample_schema)

        assert "Error generating test query with OpenAI" in str(exc_info.value)


class TestGenerateTestQueryWithAnthropic:
    """Tests for generate_test_query_with_anthropic function"""

    @patch('core.llm_processor.Anthropic')
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_test_query_success(self, mock_anthropic_class, sample_schema):
        """Test successful query generation with Anthropic"""
        # Mock Anthropic client
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Find all products with a price greater than $50."
        mock_client.messages.create.return_value = mock_response

        # Call function
        result = generate_test_query_with_anthropic(sample_schema)

        # Assertions
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Find all products" in result
        mock_client.messages.create.assert_called_once()

    @patch('core.llm_processor.Anthropic')
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_test_query_removes_quotes(self, mock_anthropic_class, sample_schema):
        """Test that quotes are removed from generated queries"""
        # Mock Anthropic client
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock response with quotes
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "'List all users by signup date.'"
        mock_client.messages.create.return_value = mock_response

        # Call function
        result = generate_test_query_with_anthropic(sample_schema)

        # Assertions
        assert not result.startswith("'")
        assert not result.endswith("'")
        assert result == "List all users by signup date."

    @patch.dict('os.environ', {}, clear=True)
    def test_generate_test_query_no_api_key(self, sample_schema):
        """Test error handling when API key is missing"""
        with pytest.raises(Exception) as exc_info:
            generate_test_query_with_anthropic(sample_schema)

        assert "ANTHROPIC_API_KEY" in str(exc_info.value)


class TestGenerateTestQuery:
    """Tests for main generate_test_query routing function"""

    @patch('core.llm_processor.generate_test_query_with_openai')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_routes_to_openai_when_key_available(self, mock_openai_func, sample_schema):
        """Test that function routes to OpenAI when API key is available"""
        mock_openai_func.return_value = "Test query"

        result = generate_test_query(sample_schema)

        mock_openai_func.assert_called_once_with(sample_schema)
        assert result == "Test query"

    @patch('core.llm_processor.generate_test_query_with_anthropic')
    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_routes_to_anthropic_when_key_available(self, mock_anthropic_func, sample_schema):
        """Test that function routes to Anthropic when API key is available"""
        mock_anthropic_func.return_value = "Test query"

        result = generate_test_query(sample_schema)

        mock_anthropic_func.assert_called_once_with(sample_schema)
        assert result == "Test query"

    @patch.dict('os.environ', {}, clear=True)
    def test_raises_error_when_no_api_keys(self, sample_schema):
        """Test that function raises error when no API keys are available"""
        with pytest.raises(Exception) as exc_info:
            generate_test_query(sample_schema)

        assert "No LLM API key available" in str(exc_info.value)

    @patch('core.llm_processor.generate_test_query_with_openai')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key', 'ANTHROPIC_API_KEY': 'test-key-2'})
    def test_prefers_openai_when_both_keys_available(self, mock_openai_func, sample_schema):
        """Test that OpenAI is preferred when both API keys are available"""
        mock_openai_func.return_value = "Test query"

        result = generate_test_query(sample_schema)

        mock_openai_func.assert_called_once_with(sample_schema)
        assert result == "Test query"
