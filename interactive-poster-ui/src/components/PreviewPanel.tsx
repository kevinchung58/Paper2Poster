import { useAppContext } from '../context/AppContext';
import { API_BASE_URL_CONFIG } from '../constants'; // For constructing image URLs
import EditableTextView from './EditableTextView'; // Import the new component

const PreviewPanel = () => {
  const { posterId, posterData, previewImageUrl, isLoading, error } = useAppContext();

  const fullPreviewUrl = previewImageUrl
    ? `${API_BASE_URL_CONFIG}${previewImageUrl}?t=${new Date().getTime()}` // Cache buster
    : null;

  return (
    // This main div will now wrap both the image preview and the text view
    <div className="w-full flex flex-col items-center space-y-6">

      {/* Original Poster Image Preview Section */}
      <div
        className="w-full max-w-2xl h-auto bg-white border border-gray-300 rounded-lg shadow-lg p-3 flex flex-col items-center justify-start min-h-[400px]" // Adjusted min-h, justify-start
      >
        <h2 className="text-xl font-semibold mb-3 text-gray-700 self-start px-1">Visual Preview</h2>

        {/* Initial Poster Creation Loading State */}
        {isLoading && !posterData && !error && (
          <div className="flex flex-col items-center justify-center flex-grow">
            <svg className="animate-spin h-10 w-10 text-blue-600 mb-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-gray-600 text-lg">Creating your poster...</p>
          </div>
        )}

        {/* Error during initial poster creation */}
        {!isLoading && error && !posterData && (
           <div className="text-red-500 bg-red-50 p-4 rounded-md w-full text-sm flex-grow flex flex-col justify-center items-center">
              <p className="font-semibold text-lg mb-2">Error Creating Poster</p>
              <p className="text-center">{error}</p>
          </div>
        )}

        {/* No poster active state */}
        {!isLoading && !error && !posterId && (
          <div className="text-center text-gray-400 flex-grow flex flex-col justify-center items-center">
            <p className="mb-2 text-lg">No active poster.</p>
            <p>Click "Create New Poster" to begin.</p>
          </div>
        )}

        {/* Poster is active, display preview based on status */}
        {posterId && posterData && (
          <div className="w-full aspect-[3/4] flex flex-col items-center justify-center relative">
            {/* Overlay for loading/pending/generating/failed states */}
            {(posterData.preview_status === "pending" || posterData.preview_status === "generating" || (isLoading && posterData)) && (
              <div className="absolute inset-0 bg-gray-500 bg-opacity-30 flex flex-col items-center justify-center z-10 rounded-md">
                <svg className="animate-spin h-8 w-8 text-white mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p className="text-white font-semibold">
                  {posterData.preview_status === "pending" ? "Preview queued..." : "Generating preview..."}
                </p>
                {isLoading && <p className="text-xs text-white/80 italic"> (Updating...)</p>}
              </div>
            )}
            {posterData.preview_status === "failed" && (
              <div className="absolute inset-0 bg-red-400 bg-opacity-80 flex flex-col items-center justify-center text-center p-4 z-10 rounded-md">
                <p className="text-white font-semibold mb-1">Preview Failed</p>
                <p className="text-xs text-white/90">{posterData.preview_last_error || "An unknown error occurred."}</p>
                <button
                    onClick={async () => { /* TODO: Implement a retry mechanism, perhaps by calling get_poster_preview again via context action */
                        console.log("Retry preview generation for:", posterId);
                        // This would ideally be an action like: appContext.retryPreviewGeneration(posterId);
                    }}
                    className="mt-2 px-3 py-1 bg-white/30 text-white text-xs rounded hover:bg-white/50"
                >
                    Retry
                </button>
              </div>
            )}

            {/* Image display (shown if completed, or shows old image during generating/pending) */}
            {(fullPreviewUrl && posterData.preview_status === "completed") || (fullPreviewUrl && (posterData.preview_status === "pending" || posterData.preview_status === "generating")) ? (
              <img
                src={fullPreviewUrl}
                alt={posterData.title || 'Poster Preview'}
                className={`w-full h-full object-contain border border-gray-200 rounded shadow-sm ${(posterData.preview_status === "pending" || posterData.preview_status === "generating") ? 'opacity-50' : ''}`}
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.onerror = null;
                  target.src = "https://via.placeholder.com/600x800.png?text=Preview+Image+Error";
                  console.error("Failed to load preview image from: ", fullPreviewUrl);
                }}
              />
            ) : ( // Placeholder if no URL or status is failed (though failed state has its own overlay)
              <div className={`w-full h-full border border-dashed border-gray-400 bg-gray-100 flex items-center justify-center rounded-md ${(posterData.preview_status === "pending" || poster_data.preview_status === "generating") ? 'opacity-50' : ''}`}>
                <p className="text-gray-500 text-center p-4">
                  {posterData.preview_status !== "failed" ? "No preview image available." : "Preview failed to generate."}
                </p>
              </div>
            )}
          </div>
        )}
      </div> {/* End of Visual Preview Section */}

      {/* New Editable Text View - Rendered if posterData exists */}
      {/* This component internally handles its own "no posterData" or "loading" state if needed,
          but it's good to also gate it here based on posterData existence. */}
      {posterData && !isLoading && ( // Show text view if data is loaded and not in a general loading state
        <div className="w-full max-w-3xl">
          <EditableTextView />
        </div>
      )}
       {isLoading && posterData && ( // If loading but there was previous data, show simpler text loading state
          <div className="w-full max-w-3xl text-center p-4 text-gray-500 italic">
              Updating text content...
          </div>
      )}

    </div>
  );
};
export default PreviewPanel;
