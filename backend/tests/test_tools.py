"""Tool registry tests."""

from app.api.tools import get_available_tools


def test_get_available_tools_includes_core_names() -> None:
    """The LLM tool list includes every planned analysis tool."""
    names = {tool["name"] for tool in get_available_tools()}
    expected = {
        "search_benchmarks",
        "fetch_model_specs",
        "analyze_capabilities",
        "find_competitors",
        "calculate_resource_requirements",
        "generate_trade_off_analysis",
        "fetch_research_papers",
        "extract_performance_metrics",
    }
    assert expected == names
    for tool in get_available_tools():
        assert "description" in tool
        assert "input_schema" in tool
