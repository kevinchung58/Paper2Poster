// Matches Pydantic schemas/models.py :: ElementStyleProperties
export interface ElementStyleProperties {
  font_size?: number; // in points (pt) for PPTX, but can be px in UI and converted
  color?: string;     // hex color string, e.g., "#FF0000"
  font_family?: string;
  // Potentially:
  // bold?: boolean;
  // italic?: boolean;
  // background_color?: string; // For the text box itself, not the slide
}

// Matches Pydantic schemas/models.py :: PosterElementStyles
export interface PosterElementStyles {
  title?: ElementStyleProperties;
  abstract?: ElementStyleProperties;
  conclusion?: ElementStyleProperties;
  section_title?: ElementStyleProperties;  // General style for all section titles
  section_content?: ElementStyleProperties; // General style for all section content
  slide_background?: string;              // Overall slide background color override (hex string)
  // For even more granularity, could allow per-section-id overrides:
  // specific_section_styles?: Record<string, { title?: ElementStyleProperties; content?: ElementStyleProperties }>;
}

// Extend existing PosterData from api.ts or define a complete one here
// For now, assuming PosterData in AppContext will be updated to include style_overrides.
// This is mostly for component prop types if we pass style objects around.

// Re-exporting from api.ts for convenience if other components need them
// and to make this file a central point for poster-related types.
export type {
    PosterSection as APIPosterSection,
    PosterData as APIPosterData,
    CreatePosterResponse as APICreatePosterResponse,
    LLMPromptResponse as APILLMPromptResponse,
    // Add other API types if needed by components directly
} from '../services/api';
