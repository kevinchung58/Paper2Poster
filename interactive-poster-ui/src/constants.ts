export const AVAILABLE_THEMES = [
  { value: "default", label: "Default Theme" },
  { value: "professional_blue", label: "Professional Blue" },
  { value: "creative_warm", label: "Creative Warm" },
  { value: "minimalist_dark", label: "Minimalist Dark" },
];

// Base URL for the backend API. Ensure this matches your backend configuration.
// It's often good to have this in a central place or environment variable.
export const API_BASE_URL_CONFIG = 'http://localhost:8000'; // Used for constructing image URLs etc.
export const API_V1_URL_CONFIG = `${API_BASE_URL_CONFIG}/api/v1`; // For actual API calls
