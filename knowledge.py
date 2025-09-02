"""
knowledge.py — Wikipedia integration helper

This module wraps the wikipedia package to fetch short summaries
for Knowledge mode in chat_core.py.

Usage:
    from knowledge import get_summary
    print(get_summary("Taj Mahal"))

Dependencies:
    pip install wikipedia
"""
import wikipedia


def get_summary(query: str, sentences: int = 3) -> str:
    """Fetch a short summary from Wikipedia.

    Parameters
    ----------
    query : str
        Search term or topic to look up.
    sentences : int, optional
        Number of sentences to return (default 3).

    Returns
    -------
    str
        Wikipedia summary text, or error message if lookup fails.
    """
    try:
        return wikipedia.summary(query, sentences=sentences, auto_suggest=True, redirect=True)
    except wikipedia.DisambiguationError as e:
        return f"The term '{query}' is ambiguous. Possible options include: {', '.join(e.options[:5])}"
    except wikipedia.PageError:
        return f"No Wikipedia page found for '{query}'."
    except Exception as e:
        return f"Wikipedia lookup failed: {e}"
