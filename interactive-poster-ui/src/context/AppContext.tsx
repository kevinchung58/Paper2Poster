import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import * as api from '../services/api';
import axios from 'axios';
import { PosterElementStyles } from '../types/posterTypes';

// --- State and Context Interfaces ---

export interface ChatMessage {
  id: string;
  sender: 'user' | 'llm' | 'system';
  text: string;
}

interface AppState {
  posterId: string | null;
  posterData: api.PosterData | null;
  previewImageUrl: string | null;
  chatMessages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  currentTargetElementId: string | null;
}

interface AppContextType extends AppState {
  startNewPoster: (topic?: string) => Promise<void>;
  sendChatMessage: (promptText: string, targetElementId?: string) => Promise<void>;
  generateAndDownloadPPTX: () => Promise<void>;
  updatePosterTheme: (newTheme: string) => Promise<void>;
  setCurrentTargetElementId: (targetId: string | null) => void;
  updateStyleOverrides: (newOverrides: PosterElementStyles) => Promise<void>;
  directUpdateElement: (targetId: string, newContent: string) => Promise<void>; // New action
}

const initialState: AppState = {
  posterId: null,
  posterData: null,
  previewImageUrl: null,
  chatMessages: [],
  isLoading: false,
  error: null,
  currentTargetElementId: null,
};

// --- Reducer Logic ---

type Action =
  | { type: 'OPERATION_START'; operationType?: string }
  | { type: 'OPERATION_FAILURE'; payload: string }
  | { type: 'NEW_POSTER_START' } // Specific start action for new poster
  | { type: 'NEW_POSTER_SUCCESS'; payload: api.CreatePosterResponse }
  | { type: 'ADD_USER_MESSAGE'; payload: { userMessage: ChatMessage } }
  | {
      type: 'UPDATE_POSTER_SUCCESS'; // Generic success for updates from LLM, theme, styles, direct edits
      payload: {
        updatedPosterData: api.PosterData;
        previewImageUrl: string;
        systemMessageText?: string; // Optional text for chat log
        llmMessage?: ChatMessage; // Specific for LLM responses
      }
    }
  | { type: 'GENERATE_PPTX_SUCCESS' }
  | { type: 'ADD_SYSTEM_MESSAGE'; payload: { messageText: string, type?: 'info' | 'error' } }
  | { type: 'SET_TARGET_ELEMENT_ID'; payload: string | null };


const appReducer = (state: AppState, action: Action): AppState => {
  switch (action.type) {
    case 'OPERATION_START':
      return { ...state, isLoading: true, error: null };
    case 'NEW_POSTER_START':
        return {
            ...state,
            isLoading: true, error: null, posterId: null, posterData: null,
            previewImageUrl: null, chatMessages: [{id: Date.now().toString(), sender: 'system', text: 'Creating new poster session...'}],
            currentTargetElementId: null,
        };
    case 'OPERATION_FAILURE':
      return { ...state, isLoading: false, error: action.payload };
    case 'NEW_POSTER_SUCCESS':
      return {
        ...state, isLoading: false, posterId: action.payload.poster_id,
        posterData: action.payload.poster_data, previewImageUrl: action.payload.preview_image_url,
        chatMessages: [
          { id: Date.now().toString(), sender: 'system', text: `New poster '${action.payload.poster_data.title}' created. You can now send prompts, change theme, or edit styles.` }
        ],
      };
    case 'ADD_USER_MESSAGE':
      return { ...state, chatMessages: [...state.chatMessages, action.payload.userMessage] };
    case 'UPDATE_POSTER_SUCCESS':
      return {
        ...state,
        isLoading: false,
        posterData: action.payload.updatedPosterData,
        previewImageUrl: action.payload.previewImageUrl,
        // Add LLM message if present, or system message if provided for other updates
        chatMessages: action.payload.llmMessage
            ? [...state.chatMessages, action.payload.llmMessage]
            : action.payload.systemMessageText
                ? [...state.chatMessages, {id: Date.now().toString(), sender: 'system', text: action.payload.systemMessageText }]
                : state.chatMessages,
      };
    case 'GENERATE_PPTX_SUCCESS':
        return { ...state, isLoading: false };
    case 'ADD_SYSTEM_MESSAGE':
        return { ...state, chatMessages: [...state.chatMessages, {id: Date.now().toString(), sender: 'system', text: action.payload.messageText}] };
    case 'SET_TARGET_ELEMENT_ID':
        return { ...state, currentTargetElementId: action.payload };
    default:
      return state;
  }
};

// --- Context and Provider ---
const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Polling logic for preview status
  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;

    const pollPosterStatus = async () => {
      if (!state.posterId) { // Should not happen if status is pending/generating
        if (intervalId) clearInterval(intervalId);
        return;
      }
      try {
        console.log(`Polling for poster ${state.posterId} status: ${state.posterData?.preview_status}`);
        const posterStateResponse = await api.getPosterState(state.posterId); // Fetches full PosterState

        // Dispatch an action that updates posterData including preview_status and preview_image_url
        // UPDATE_POSTER_SUCCESS can be used if its payload structure matches.
        // The backend's /posters/{poster_id} endpoint returns a Poster schema (which is PosterData like).
        // Ensure the response from getPosterState matches what UPDATE_POSTER_SUCCESS expects for updatedPosterData.
        // The PosterState from backend contains poster_data which is our PosterData.
        dispatch({
          type: 'UPDATE_POSTER_SUCCESS',
          payload: {
            updatedPosterData: posterStateResponse.poster_data, // Extract poster_data from PosterState
            previewImageUrl: posterStateResponse.poster_data.preview_image_url || state.previewImageUrl, // Use new if available
            systemMessageText: `Preview status for '${posterStateResponse.poster_data.title}' is now ${posterStateResponse.poster_data.preview_status}.`
          }
        });

        if (posterStateResponse.poster_data.preview_status === "completed" || posterStateResponse.poster_data.preview_status === "failed") {
          if (intervalId) clearInterval(intervalId);
          console.log(`Polling stopped for poster ${state.posterId}. Final status: ${posterStateResponse.poster_data.preview_status}`);
        }
      } catch (error) {
        console.error("Polling error:", error);
        // Optionally dispatch a specific polling failure, or set a general error
        // dispatch({ type: 'OPERATION_FAILURE', payload: 'Failed to poll for preview status.' });
        if (intervalId) clearInterval(intervalId);
      }
    };

    if (state.posterId && state.posterData && (state.posterData.preview_status === "pending" || state.posterData.preview_status === "generating")) {
      intervalId = setInterval(pollPosterStatus, 3000); // Poll every 3 seconds
      console.log(`Polling started for poster ${state.posterId}`);
    }

    return () => { // Cleanup function for the effect
      if (intervalId) {
        clearInterval(intervalId);
        console.log(`Polling interval cleared for poster ${state.posterId} due to effect cleanup.`);
      }
    };
  }, [state.posterId, state.posterData, state.posterData?.preview_status, dispatch]); // Added state.posterData to deps for initial status check


  const startNewPoster = async (topic?: string) => {
    dispatch({ type: 'NEW_POSTER_START' });
    try {
      const response = await api.createPosterSession(topic);
      dispatch({ type: 'NEW_POSTER_SUCCESS', payload: response });
    } catch (err) {
      const errorMsg = axios.isAxiosError(err) && err.response ? `Error ${err.response.status}: ${err.response.data.detail || err.message}` : (err as Error).message;
      dispatch({ type: 'OPERATION_FAILURE', payload: errorMsg });
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error creating poster: ${errorMsg}`, type: 'error' } });
    }
  };

  const sendChatMessage = async (promptText: string, targetElementId?: string) => {
    if (!state.posterId) { /* ... error handling ... */ return; }
    dispatch({ type: 'ADD_USER_MESSAGE', payload: { userMessage: { id: Date.now().toString(), sender: 'user', text: promptText } }});
    dispatch({ type: 'OPERATION_START' });
    try {
      const response = await api.sendLLMPrompt(state.posterId, promptText, targetElementId);
      dispatch({
        type: 'UPDATE_POSTER_SUCCESS',
        payload: {
          llmMessage: { id: (Date.now() + 1).toString(), sender: 'llm', text: response.llm_response_text },
          updatedPosterData: response.updated_poster_data,
          previewImageUrl: response.preview_image_url,
        },
      });
    } catch (err) { /* ... error handling ... */
        const errorMsg = axios.isAxiosError(err) && err.response ? `LLM Error: ${err.response.data.detail || err.message}` : (err as Error).message;
        dispatch({ type: 'OPERATION_FAILURE', payload: errorMsg });
        dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error: ${errorMsg}`, type: 'error' }});
    }
  };

  const updatePosterTheme = async (newTheme: string) => {
    if (!state.posterId || !state.posterData || state.posterData.selected_theme === newTheme) { /* ... checks ... */ return; }
    dispatch({ type: 'OPERATION_START' });
    dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Updating theme to '${newTheme}'...`, type: 'info' } });
    try {
      const response = await api.sendLLMPrompt(state.posterId, undefined, undefined, newTheme, undefined, false);
      dispatch({
        type: 'UPDATE_POSTER_SUCCESS',
        payload: {
          updatedPosterData: response.updated_poster_data,
          previewImageUrl: response.preview_image_url,
          systemMessageText: response.llm_response_text || `Theme updated to ${newTheme}.`
        }
      });
    } catch (err) { /* ... error handling ... */
        const errorMsg = axios.isAxiosError(err) && err.response ? `Theme Error: ${err.response.data.detail || err.message}` : (err as Error).message;
        dispatch({ type: 'OPERATION_FAILURE', payload: errorMsg });
        dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error: ${errorMsg}`, type: 'error' }});
    }
  };

  const updateStyleOverrides = async (newOverrides: PosterElementStyles) => {
    if (!state.posterId) { /* ... error handling ... */ return; }
    dispatch({ type: 'OPERATION_START' });
    dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: 'Applying style overrides...', type: 'info' } });
    try {
      const response = await api.sendLLMPrompt(state.posterId, undefined, undefined, undefined, newOverrides, false);
      dispatch({
        type: 'UPDATE_POSTER_SUCCESS',
        payload: {
          updatedPosterData: response.updated_poster_data,
          previewImageUrl: response.preview_image_url,
          systemMessageText: response.llm_response_text || 'Style overrides applied.'
        }
      });
    } catch (err) { /* ... error handling ... */
        const errorMsg = axios.isAxiosError(err) && err.response ? `Style Error: ${err.response.data.detail || err.message}` : (err as Error).message;
        dispatch({ type: 'OPERATION_FAILURE', payload: errorMsg });
        dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error: ${errorMsg}`, type: 'error' }});
    }
  };

  const directUpdateElement = async (targetId: string, newContent: string) => {
    if (!state.posterId) {
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: 'Error: No active poster. Cannot update element.', type: 'error' } });
      return;
    }
    dispatch({ type: 'OPERATION_START' });
    try {
      const response = await api.sendLLMPrompt(
        state.posterId, newContent, targetId,
        undefined, undefined, true // is_direct_update = true
      );
      dispatch({
        type: 'UPDATE_POSTER_SUCCESS',
        payload: {
          updatedPosterData: response.updated_poster_data,
          previewImageUrl: response.preview_image_url,
          systemMessageText: response.llm_response_text || `Element '${targetId}' directly updated.`
        }
      });
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || `Failed to directly update element '${targetId}'.`;
      dispatch({ type: 'OPERATION_FAILURE', payload: errorMsg });
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error updating ${targetId}: ${errorMsg}`, type: 'error' } });
    }
  };

  const setCurrentTargetElementId = (targetId: string | null) => {
    dispatch({ type: 'SET_TARGET_ELEMENT_ID', payload: targetId });
  };

  const generateAndDownloadPPTX = async () => {
    if (!state.posterId) { /* ... error handling ... */ return; }
    dispatch({ type: 'OPERATION_START' });
    dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: 'Generating PPTX file...', type: 'info' } });
    try {
      const response = await api.triggerPPTXGenerationOnBackend(state.posterId);
      const backendRootUrl = api.API_V1_URL_CONFIG.replace('/api/v1', '');
      const fullDownloadUrl = `${backendRootUrl}${response.download_url}`;
      window.open(fullDownloadUrl, '_blank');
      dispatch({ type: 'GENERATE_PPTX_SUCCESS' });
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: response.message || 'PPTX generated and download started.', type: 'info' } });
    } catch (err) { /* ... error handling ... */
        const errorMsg = axios.isAxiosError(err) && err.response ? `PPTX Error: ${err.response.data.detail || err.message}` : (err as Error).message;
        dispatch({ type: 'OPERATION_FAILURE', payload: errorMsg });
        dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error: ${errorMsg}`, type: 'error' }});
    }
  };

  return (
    <AppContext.Provider value={{ ...state, startNewPoster, sendChatMessage, generateAndDownloadPPTX, updatePosterTheme, setCurrentTargetElementId, updateStyleOverrides, directUpdateElement }}>
      {children}
    </AppContext.Provider>
  );
};

// --- Custom Hook ---
export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
