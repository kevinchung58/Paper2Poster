import axios from 'axios';
import { API_V1_URL_CONFIG } from '../constants';

// --- Style Override Types (matching backend Pydantic schemas) ---
export interface ElementStyleProperties {
  font_size?: number;
  color?: string;     // hex color string, e.g., "#FF0000"
  font_family?: string;
}

export interface PosterElementStyles {
  title?: ElementStyleProperties;
  abstract?: ElementStyleProperties;
  conclusion?: ElementStyleProperties;
  section_title?: ElementStyleProperties;
  section_content?: ElementStyleProperties;
  slide_background?: string;
}

// --- Request/Response Interfaces (matching backend Pydantic models) ---

export interface PosterSection {
  section_id: string;
  section_title: string;
  section_content: string;
  section_images: string[];
}

export interface PosterData {
  title: string;
  abstract?: string;
  sections: PosterSection[];
  conclusion?: string;
  theme: string;
  selected_theme: string;
  style_overrides?: PosterElementStyles | null;
  preview_status: "pending" | "generating" | "completed" | "failed"; // Added
  preview_last_error?: string | null; // Added
}

export interface CreatePosterRequest {
  topic?: string;
  template_id?: string;
}

export interface CreatePosterResponse {
  poster_id: string;
  poster_data: PosterData; // Should include selected_theme and style_overrides
  preview_image_url: string;
}

export interface PosterState { // Represents full state if fetched, similar to PosterData
  poster_id: string;
  poster_data: PosterData;
  last_modified: string;
  pptx_file_path?: string;
  preview_image_path?: string;
}

// Updated to match backend's OriginalLLMPromptRequest Pydantic schema
export interface LLMPromptRequest {
  prompt_text?: string; // Now optional
  target_element_id?: string;
  selected_theme?: string;
  style_overrides?: PosterElementStyles | null;
}

export interface LLMPromptResponse {
  poster_id: string;
  llm_response_text: string;
  updated_poster_data: PosterData; // Should include selected_theme and style_overrides
  preview_image_url: string;
}

export interface GeneratePPTXResponse {
  poster_id: string;
  download_url: string;
  message: string;
}


// --- API Functions ---

export const createPosterSession = async (topic?: string): Promise<CreatePosterResponse> => {
  const requestBody: CreatePosterRequest = {};
  if (topic) {
    requestBody.topic = topic;
  }
  const response = await axios.post<CreatePosterResponse>(`${API_V1_URL_CONFIG}/posters`, requestBody);
  return response.data;
};

export const getPosterState = async (posterId: string): Promise<PosterState> => {
  // Note: PosterState might be too broad if only PosterData is needed by most of UI.
  // For now, assuming it's okay. This endpoint returns the DB representation.
  const response = await axios.get<PosterState>(`${API_V1_URL_CONFIG}/posters/${posterId}`);
  return response.data;
};

export const sendLLMPrompt = async (
  posterId: string,
  promptText?: string,
  targetElementId?: string,
  selectedTheme?: string,
  styleOverrides?: PosterElementStyles | null,
  isDirectUpdate?: boolean // New optional parameter
): Promise<LLMPromptResponse> => {
  const requestBody: LLMPromptRequest = {};

  if (promptText !== undefined) requestBody.prompt_text = promptText;
  if (targetElementId !== undefined) requestBody.target_element_id = targetElementId;
  if (selectedTheme !== undefined) requestBody.selected_theme = selectedTheme;
  if (styleOverrides !== undefined) requestBody.style_overrides = styleOverrides;
  if (isDirectUpdate !== undefined) requestBody.is_direct_update = isDirectUpdate; // Add to request

  // Ensure at least one relevant field is present if API requires it.
  // The backend /prompt endpoint can now handle theme-only or style-only updates.
  // If all are undefined, requestBody will be {}.
  // This is fine as backend /prompt can handle empty body if it means "no specific update, just get current state"
  // or simply do nothing if no specific update fields are present.
  // For our use (theme update, style update, prompt), at least one will be there.

  const response = await axios.post<LLMPromptResponse>(
    `${API_V1_URL_CONFIG}/posters/${posterId}/prompt`,
    requestBody
  );
  return response.data;
};

export const triggerPPTXGenerationOnBackend = async (posterId: string): Promise<GeneratePPTXResponse> => {
    const response = await axios.post<GeneratePPTXResponse>(`${API_V1_URL_CONFIG}/posters/${posterId}/generate_pptx`);
    return response.data;
};

export const getPPTXDownloadUrl = (posterId: string): string => {
  return `${API_V1_URL_CONFIG}/posters/${posterId}/download_pptx`;
};
