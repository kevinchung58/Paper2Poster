from enum import Enum

class PosterElement(str, Enum):
    """
    Enum for identifying targetable elements within the poster for updates.
    """
    POSTER_TITLE = "poster_title"
    POSTER_ABSTRACT = "poster_abstract"
    POSTER_CONCLUSION = "poster_conclusion"

    # Dynamic section elements will be handled by prefix, but we can define the prefixes or types
    SECTION_TITLE = "section_title"
    SECTION_CONTENT = "section_content"

    # A helper to check for section-related prefixes
    @staticmethod
    def is_section_element(element_id: str) -> bool:
        return element_id.startswith("section_")