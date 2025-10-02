import React, { createContext, useContext, useReducer, ReactNode, useEffect } from 'react';
import * as api from '../services/api';
import { PosterElementStyles } from '../types/posterTypes';

// --- Custom Error Type ---
interface ApiError {
    response?: {
        data?: {
            detail?: string;
        };
    };
    message?: string;
}

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
  directUpdateElement: (targetId: string, newContent: string) => Promise<void>;
  updateSectionImageUrls: (sectionId: string, newImageUrls: string[]) => Promise<void>;
  uploadImageForSection: (sectionId: string, file: File) => Promise<void>;
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
  | { type: 'NEW_POSTER_START' }
  | { type: 'NEW_POSTER_SUCCESS'; payload: api.CreatePosterResponse }
  | { type: 'ADD_USER_MESSAGE'; payload: { userMessage: ChatMessage } }
  | {
      type: 'UPDATE_POSTER_SUCCESS';
      payload: {
        updatedPosterData: api.PosterData;
        previewImageUrl: string | null;
        systemMessageText?: string;
        llmMessage?: ChatMessage;
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
            ...state, isLoading: true, error: null, posterId: null, posterData: null,
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

  const handlePosterUpdateResponse = (
    response: api.LLMPromptResponse | api.CreatePosterResponse,
    systemMessageText?: string,
    llmMessageText?: string
  ) => {
    const payload: Extract<Action, { type: 'UPDATE_POSTER_SUCCESS' }>['payload'] = {
      updatedPosterData: response.poster_data,
      previewImageUrl: response.preview_image_url,
    };
    if (llmMessageText) {
      payload.llmMessage = { id: (Date.now() + 1).toString(), sender: 'llm', text: llmMessageText };
    } else if (systemMessageText) {
      payload.systemMessageText = systemMessageText;
    }
    dispatch({ type: 'UPDATE_POSTER_SUCCESS', payload });
  };

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;
    const pollPosterStatus = async () => {
      if (!state.posterId) { if (intervalId) clearInterval(intervalId); return; }
      try {
        const posterDataResponse = await api.getPosterState(state.posterId);
        dispatch({
          type: 'UPDATE_POSTER_SUCCESS',
          payload: {
            updatedPosterData: posterDataResponse,
            previewImageUrl: posterDataResponse.preview_image_url || state.previewImageUrl,
            systemMessageText: posterDataResponse.preview_status !== state.posterData?.preview_status ?
                               `Preview status for '${posterDataResponse.title}' is now ${posterDataResponse.preview_status}.` : undefined
          }
        });
        if (posterDataResponse.preview_status === "completed" || posterDataResponse.preview_status === "failed") {
          if (intervalId) clearInterval(intervalId);
        }
      } catch (error) { if (intervalId) clearInterval(intervalId); console.error("Polling error:", error); }
    };
    if (state.posterId && state.posterData && (state.posterData.preview_status === "pending" || state.posterData.preview_status === "generating")) {
      intervalId = setInterval(pollPosterStatus, 3000);
    }
    return () => { if (intervalId) clearInterval(intervalId); };
  }, [state.posterId, state.posterData, state.posterData?.preview_status, state.previewImageUrl, dispatch]);

  const startNewPoster = async (topic?: string) => {
    dispatch({ type: 'NEW_POSTER_START' });
    try {
      const response = await api.createPosterSession(topic);
      dispatch({ type: 'NEW_POSTER_SUCCESS', payload: response });
    } catch (err) {
      const error = err as ApiError;
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to start a new poster session.';
      dispatch({ type: 'OPERATION_FAILURE', payload: errorMessage });
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error: ${errorMessage}`, type: 'error' } });
    }
  };

  const sendChatMessage = async (promptText: string, targetElementId?: string) => {
    if (!state.posterId) { return; }
    dispatch({ type: 'ADD_USER_MESSAGE', payload: { userMessage: { id: Date.now().toString(), sender: 'user', text: promptText } }});
    dispatch({ type: 'OPERATION_START' });
    try {
      const response = await api.sendLLMPrompt(state.posterId, promptText, targetElementId);
      handlePosterUpdateResponse(response, undefined, response.llm_response_text);
    } catch (err) {
      const error = err as ApiError;
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to send prompt.';
      dispatch({ type: 'OPERATION_FAILURE', payload: errorMessage });
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error: ${errorMessage}`, type: 'error' } });
    }
  };

  const updatePosterTheme = async (newTheme: string) => {
    if (!state.posterId || !state.posterData || state.posterData.selected_theme === newTheme) { return; }
    dispatch({ type: 'OPERATION_START' });
    dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Updating theme to '${newTheme}'...`, type: 'info' } });
    try {
      const response = await api.sendLLMPrompt(state.posterId, undefined, undefined, newTheme, undefined, true);
      handlePosterUpdateResponse(response, response.llm_response_text || `Theme updated to ${newTheme}.`);
    } catch (err) {
      const error = err as ApiError;
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to update theme.';
      dispatch({ type: 'OPERATION_FAILURE', payload: errorMessage });
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error: ${errorMessage}`, type: 'error' } });
    }
  };

  const updateStyleOverrides = async (newOverrides: PosterElementStyles) => {
    if (!state.posterId) { return; }
    dispatch({ type: 'OPERATION_START' });
    dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: 'Applying style overrides...', type: 'info' } });
    try {
      const response = await api.sendLLMPrompt(state.posterId, undefined, undefined, undefined, newOverrides, true);
      handlePosterUpdateResponse(response, response.llm_response_text || 'Style overrides applied.');
    } catch (err) {
      const error = err as ApiError;
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to apply styles.';
      dispatch({ type: 'OPERATION_FAILURE', payload: errorMessage });
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error: ${errorMessage}`, type: 'error' } });
    }
  };

  const directUpdateElement = async (targetId: string, newContent: string) => {
    if (!state.posterId) { return; }
    dispatch({ type: 'OPERATION_START' });
    try {
      const response = await api.sendLLMPrompt(
        state.posterId, newContent, targetId,
        undefined, undefined, true
      );
      handlePosterUpdateResponse(response, response.llm_response_text || `Element '${targetId}' updated.`);
    } catch (err) {
      const error = err as ApiError;
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to update element.';
      dispatch({ type: 'OPERATION_FAILURE', payload: errorMessage });
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error: ${errorMessage}`, type: 'error' } });
    }
  };

  const updateSectionImageUrls = async (sectionId: string, newImageUrls: string[]) => {
    if (!state.posterId || !state.posterData) {
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: 'Error: No active poster to update image URLs.', type: 'error' } });
      return;
    }
    const currentSections = JSON.parse(JSON.stringify(state.posterData.sections || [])) as api.PosterSection[];
    const sectionIndex = currentSections.findIndex(s => s.section_id === sectionId);
    if (sectionIndex === -1) {
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error: Section ${sectionId} not found.`, type: 'error' } });
      return;
    }
    currentSections[sectionIndex].image_urls = newImageUrls;

    dispatch({ type: 'OPERATION_START' });
    const systemMessageText = `Image URLs for section '${currentSections[sectionIndex].section_title || sectionId}' updated.`;
    dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: systemMessageText, type: 'info' }});

    try {
      const response = await api.sendLLMPrompt(
        state.posterId, undefined, undefined, undefined, undefined, true, currentSections
      );
      handlePosterUpdateResponse(response, response.llm_response_text || systemMessageText);
    } catch (err) {
      const error = err as ApiError;
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to update image URLs.';
      dispatch({ type: 'OPERATION_FAILURE', payload: errorMsg });
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error: ${errorMsg}`, type: 'error' } });
    }
  };

  const uploadImageForSection = async (sectionId: string, file: File) => {
    if (!state.posterId) {
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: 'Error: No active poster to upload image for.', type: 'error' } });
      return;
    }

    dispatch({ type: 'OPERATION_START', operationType: 'uploadImage' });
    const tempSystemMessage = `Uploading image '${file.name}' for section...`;
    dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: tempSystemMessage, type: 'info' } });

    try {
      const updatedPosterDataFromUpload = await api.uploadSectionImage(state.posterId, sectionId, file);
      dispatch({
        type: 'UPDATE_POSTER_SUCCESS',
        payload: {
          updatedPosterData: updatedPosterDataFromUpload,
          previewImageUrl: updatedPosterDataFromUpload.preview_image_url,
          systemMessageText: `Image '${file.name}' uploaded for section. Preview is updating.`
        }
      });
    } catch (err) {
      const error = err as ApiError;
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to upload image.';
      dispatch({ type: 'OPERATION_FAILURE', payload: errorMessage });
      dispatch({ type: 'ADD_SYSTEM_MESSAGE', payload: { messageText: `Error uploading '${file.name}': ${errorMessage}`, type: 'error' } });
    }
  };

  const setCurrentTargetElementId = (targetId: string | null) => {
    dispatch({ type: 'SET_TARGET_ELEMENT_ID', payload: targetId });
  };

  const generateAndDownloadPPTX = async () => { /* ... existing code ... */ };

  return (
    <AppContext.Provider value={{ ...state, startNewPoster, sendChatMessage, generateAndDownloadPPTX, updatePosterTheme, setCurrentTargetElementId, updateStyleOverrides, directUpdateElement, updateSectionImageUrls, uploadImageForSection }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};