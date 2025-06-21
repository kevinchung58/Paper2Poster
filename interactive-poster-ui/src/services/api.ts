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

export interface PosterSection { // Represents a section's data, used in PosterData and for updates
  section_id: string;
  section_title: string;
  section_content: string;
  image_urls: string[]; // Standardized name
}

export interface PosterData {
  poster_id: string; // Added poster_id here as it's part of the core Poster data from backend
  title: string;
  abstract?: string | null;
  sections: PosterSection[];
  conclusion?: string | null;
  theme: string;
  selected_theme: string;
  style_overrides?: PosterElementStyles | null;
  preview_status: "pending" | "generating" | "completed" | "failed";
  preview_last_error?: string | null;
  last_modified: string; // Added last_modified from backend Poster schema
  pptx_file_path?: string | null; // Added from backend Poster schema
  preview_image_path?: string | null; // Added from backend Poster schema
}

export interface CreatePosterRequest { // For initial POST /posters
  topic?: string;
  template_id?: string;
}

export interface CreatePosterResponse { // Response from POST /posters
  poster_id: string;
  poster_data: PosterData;
  preview_image_url: string;
}

// This was for GET /posters/{poster_id} which returns a Poster Pydantic model
// which is essentially PosterData.
export type GetPosterStateResponse = PosterData;


// Updated to match backend's OriginalLLMPromptRequest Pydantic schema,
// and to allow sending 'sections' for direct updates.
export interface LLMPromptRequest {
  prompt_text?: string;
  target_element_id?: string;
  selected_theme?: string;
  style_overrides?: PosterElementStyles | null;
  is_direct_update?: boolean;
  sections?: PosterSection[]; // For sending updated sections list during direct updates
  // Other specific fields from PosterUpdate could be added if needed for direct updates,
  // e.g. title?: string, abstract?: string etc. if not using target_element_id for them.
}

export interface LLMPromptResponse { // Response from POST /prompt
  poster_id: string;
  llm_response_text: string;
  updated_poster_data: PosterData;
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

// Fetches the full Poster data object
export const getPosterState = async (posterId: string): Promise<GetPosterStateResponse> => {
  const response = await axios.get<GetPosterStateResponse>(`${API_V1_URL_CONFIG}/posters/${posterId}`);
  return response.data;
};

export const sendLLMPrompt = async (
  posterId: string,
  promptText?: string,
  targetElementId?: string,
  selectedTheme?: string,
  styleOverrides?: PosterElementStyles | null,
  isDirectUpdate?: boolean,
  sectionsPayload?: PosterSection[] // For direct update of sections array
): Promise<LLMPromptResponse> => {
  const requestBody: LLMPromptRequest = {};

  if (promptText !== undefined) requestBody.prompt_text = promptText;
  if (targetElementId !== undefined) requestBody.target_element_id = targetElementId;
  if (selectedTheme !== undefined) requestBody.selected_theme = selectedTheme;
  if (styleOverrides !== undefined) requestBody.style_overrides = styleOverrides;
  if (isDirectUpdate !== undefined) requestBody.is_direct_update = isDirectUpdate;
  if (sectionsPayload !== undefined) requestBody.sections = sectionsPayload; // Add sections if provided

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

// For POST /posters/{poster_id}/sections/{section_id}/upload_image
// The backend returns the full updated Poster (which is PosterData type on frontend)
export const uploadSectionImage = async (
  posterId: string,
  sectionId: string,
  file: File
): Promise<PosterData> => {
  const formData = new FormData();
  formData.append("image_file", file); // "image_file" must match the backend File(...) parameter name

  const response = await axios.post<PosterData>( // Expecting PosterData in response
    `${API_V1_URL_CONFIG}/posters/${posterId}/sections/${sectionId}/upload_image`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
  return response.data;
};
