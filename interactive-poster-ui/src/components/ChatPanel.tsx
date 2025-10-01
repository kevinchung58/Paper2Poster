import React, { useState, useEffect, useRef } from 'react';
import { useAppContext } from '../context/AppContext';
import { AVAILABLE_THEMES } from '../constants';
import StyleControls from './StyleControls'; // Import the new component

const ChatPanel = () => {
  const {
    posterId,
    posterData,
    startNewPoster,
    sendChatMessage,
    generateAndDownloadPPTX,
    updatePosterTheme,
    isLoading,
    error,
    chatMessages,
    currentTargetElementId,
    setCurrentTargetElementId
  } = useAppContext();

  const [topic, setTopic] = useState('');
  const [prompt, setPrompt] = useState('');
  const [selectableTargets, setSelectableTargets] = useState<Array<{ value: string; label: string }>>([]);
  const chatLogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (posterData) {
      const targets = [{ value: "", label: "▶ Entire Poster / General" }];
      targets.push({ value: "poster_title", label: "Poster Title" });
      if (posterData.abstract !== undefined) {
        targets.push({ value: "poster_abstract", label: "Poster Abstract" });
      }
      posterData.sections.forEach((section, index) => {
        const sectionLabelPrefix = section.section_title ? `Section: ${section.section_title}` : `Section ${index + 1}`;
        targets.push({ value: `section_${section.section_id}_title`, label: `${sectionLabelPrefix} - Title` });
        targets.push({ value: `section_${section.section_id}_content`, label: `${sectionLabelPrefix} - Content` });
      });
      if (posterData.conclusion !== undefined) {
        targets.push({ value: "poster_conclusion", label: "Poster Conclusion" });
      }
      setSelectableTargets(targets);
      if (currentTargetElementId && !targets.find(t => t.value === currentTargetElementId)) {
        setCurrentTargetElementId(null);
      }
    } else {
      setSelectableTargets([{ value: "", label: "▶ Entire Poster / General" }]);
      if (currentTargetElementId !== null) {
          setCurrentTargetElementId(null);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [posterData]);

  const handleNewPoster = () => {
    startNewPoster(topic || undefined);
    setTopic('');
  };

  const handleSendPrompt = () => {
    if (!prompt.trim() || !posterId) return;
    sendChatMessage(prompt.trim(), currentTargetElementId || undefined);
    setPrompt('');
  };

  useEffect(() => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [chatMessages]);

  return (
    <div className="h-full flex flex-col border rounded-lg p-4 bg-white shadow-sm space-y-4"> {/* Added space-y-4 for spacing between main children */}

      {/* Poster Controls Section (Topic, New Poster, Download, Theme) */}
      <div className="pb-4 border-b">
        <h2 className="text-xl font-semibold text-gray-700 mb-3">Poster Controls</h2>
        <div className="space-y-3"> {/* Spacing for controls */}
          <div>
            <label htmlFor="topicInput" className="block text-sm font-medium text-gray-600 mb-1">
              Poster Topic (Optional)
            </label>
            <input
              id="topicInput"
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., 'AI in Healthcare'"
              className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            />
          </div>
          <button
            onClick={handleNewPoster}
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-2 px-4 rounded-md transition duration-150 ease-in-out shadow"
          >
            {isLoading && !posterId ? 'Creating Poster...' : 'Create New Poster'}
          </button>
          <button
            onClick={() => posterId && generateAndDownloadPPTX()}
            disabled={!posterId || isLoading}
            className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white font-semibold py-2 px-4 rounded-md transition duration-150 ease-in-out shadow"
          >
            {isLoading && posterId ? 'Processing...' : 'Generate & Download PPTX'}
          </button>
          {posterId && posterData && (
            <div>
              <label htmlFor="theme-select" className="block text-sm font-medium text-gray-600 mb-1">
                Poster Theme:
              </label>
              <select
                id="theme-select"
                value={posterData.selected_theme || 'default'}
                onChange={(e) => updatePosterTheme(e.target.value)}
                disabled={isLoading}
                className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 text-sm"
              >
                {AVAILABLE_THEMES.map(theme => (
                  <option key={theme.value} value={theme.value}>
                    {theme.label}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Granular Style Controls - Rendered if a poster is active */}
      {posterId && <StyleControls />}

      {/* Error Display Area */}
      {error && (
        <div className="my-2 p-3 bg-red-100 border border-red-300 text-red-600 rounded-md text-sm">
          <p className="font-medium">Operation Error:</p>
          <p>{error}</p>
        </div>
      )}

      {/* Chat Log Section - flex-grow will make this take available space */}
      <div className="flex flex-col flex-grow min-h-[150px]"> {/* Ensure chat log can grow */}
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Chat Log</h3>
        <div
          ref={chatLogRef}
          className="flex-grow p-3 border rounded-md bg-gray-50 overflow-y-auto shadow-inner"
        >
          {chatMessages.length === 0 && !isLoading && (
            <p className="text-sm text-gray-400 italic text-center py-4">
              {posterId ? "Chat log is empty. Send a prompt below." : "Create a new poster to begin."}
            </p>
          )}
          {chatMessages.map((msg) => (
            <div
              key={msg.id}
              className={`mb-3 py-2 px-3 rounded-xl max-w-[85%] clear-both ${
              msg.sender === 'user'
                ? 'bg-blue-500 text-white float-right'
                : msg.sender === 'llm'
                ? 'bg-green-500 text-white float-left'
                : 'bg-gray-300 text-gray-700 text-xs italic text-center mx-auto w-full max-w-[95%]'
            }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
            </div>
          ))}
           {isLoading && posterId && (
              <div className="text-center py-2">
                  <p className="text-sm text-blue-600 italic">Processing...</p> {/* Generic processing message */}
              </div>
          )}
        </div>
      </div>

      {/* LLM Prompt Input Section */}
      <div className="pt-3 border-t"> {/* Removed mt-auto to allow chatlog to grow */}
        {posterId && (
          <div className="mb-3">
            <label htmlFor="target-prompt-select" className="block text-sm font-medium text-gray-600 mb-1">
              Target Prompt To:
            </label>
            <select
              id="target-prompt-select"
              value={currentTargetElementId || ""}
              onChange={(e) => setCurrentTargetElementId(e.target.value === "" ? null : e.target.value)}
              disabled={isLoading || !posterData}
              className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500 text-sm"
            >
              {selectableTargets.map(target => (
                <option key={target.value} value={target.value}>
                  {target.label}
                </option>
              ))}
            </select>
          </div>
        )}
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !e.shiftKey && prompt.trim() && posterId && !isLoading) {
              e.preventDefault();
              handleSendPrompt();
            }
          }}
          className="w-full p-2 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500 text-sm"
          placeholder={posterId ? "Type your prompt for the LLM..." : "Create a poster to enable chat."}
          rows={3}
          disabled={!posterId || isLoading}
        />
        <button
          onClick={handleSendPrompt}
          disabled={!posterId || isLoading || !prompt.trim()}
          className="mt-2 w-full bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white font-semibold py-2 px-4 rounded-md transition duration-150 ease-in-out shadow"
        >
          Send Prompt to LLM
        </button>
      </div>
    </div>
  );
};
export default ChatPanel;
