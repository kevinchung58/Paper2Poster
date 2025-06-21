import React, { useState } from 'react';
import { useAppContext } from '../context/AppContext';
// PosterData type from context will include image_urls in its sections

const EditableTextView = () => {
  const { posterData, isLoading, directUpdateElement, updateSectionImageUrls } = useAppContext(); // Added updateSectionImageUrls

  const [editingTargetId, setEditingTargetId] = useState<string | null>(null);
  const [editingValue, setEditingValue] = useState<string>("");
  const [originalValue, setOriginalValue] = useState<string>("");

  const handleEditClick = (targetId: string, currentValue: string | undefined | null) => {
    setEditingTargetId(targetId);
    const cv = currentValue ?? "";
    setEditingValue(cv);
    setOriginalValue(cv);
  };

  const handleBlurSave = async () => {
    if (editingTargetId && editingValue !== originalValue) {
      await directUpdateElement(editingTargetId, editingValue);
    }
    setEditingTargetId(null);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !(event.target instanceof HTMLTextAreaElement && event.shiftKey)) {
      event.preventDefault();
      handleBlurSave();
    } else if (event.key === 'Escape') {
      setEditingTargetId(null);
    }
  };

  if (isLoading && !posterData) {
    return <p className="text-center p-4 text-gray-500 italic">Loading poster data for text view...</p>;
  }

  if (!posterData) {
    return (
      <div className="my-6 p-4 border rounded-lg bg-gray-50 shadow text-center">
        <p className="text-gray-500">No poster data available. Create a new poster to see its text content here.</p>
      </div>
    );
  }

  const renderTextPlaceholder = (text: string | undefined | null, defaultPlaceholder: string = "Click to edit...") => {
    return text || defaultPlaceholder;
  };

  const renderEditableField = (
    currentValue: string | undefined | null,
    targetId: string,
    // label: string, // Label is now rendered outside this helper
    isTextArea: boolean = false,
    defaultPlaceholder: string = "Click to edit..."
  ) => {
    if (editingTargetId === targetId) {
      return isTextArea ? (
        <textarea
          value={editingValue}
          onChange={(e) => setEditingValue(e.target.value)}
          onBlur={handleBlurSave}
          onKeyDown={handleKeyDown}
          autoFocus
          className="text-md p-1 border border-blue-500 rounded w-full whitespace-pre-wrap shadow-sm"
          rows={5}
        />
      ) : (
        <input
          type="text"
          value={editingValue}
          onChange={(e) => setEditingValue(e.target.value)}
          onBlur={handleBlurSave}
          onKeyDown={handleKeyDown}
          autoFocus
          className={`${
            targetId === 'poster_title' ? 'text-2xl font-bold' :
            targetId.endsWith('_title') ? 'text-lg font-semibold' : 'text-md'
          } p-1 border border-blue-500 rounded w-full shadow-sm`}
        />
      );
    }
    return (
      <p
        className={`${
          targetId === 'poster_title' ? 'text-2xl font-bold' :
          targetId.endsWith('_title') ? 'text-lg font-semibold' : 'text-md'
        } editable-content p-1 border border-transparent hover:border-gray-300 rounded cursor-pointer whitespace-pre-wrap min-h-[1.5em]`} // Added min-h for empty state clickability
        onClick={() => handleEditClick(targetId, currentValue)}
      >
        {renderTextPlaceholder(currentValue, defaultPlaceholder)}
      </p>
    );
  };

  return (
    <div className="my-6 p-4 md:p-6 border rounded-lg bg-white shadow-md">
      <h3 className="text-xl font-semibold mb-4 border-b pb-2 text-gray-700">
        Poster Content (Click text to edit)
      </h3>

      <div className="mb-4 p-3 rounded-md hover:bg-gray-50 editable-text-section" data-target-id="poster_title">
        <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">Title</label>
        {renderEditableField(posterData.title, "poster_title", false, "Untitled Poster")}
      </div>

      {posterData.abstract !== undefined && (
        <div className="mb-4 p-3 rounded-md hover:bg-gray-50 editable-text-section" data-target-id="poster_abstract">
          <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">Abstract</label>
          {renderEditableField(posterData.abstract, "poster_abstract", true, "No abstract provided.")}
        </div>
      )}

      {posterData.sections && posterData.sections.length > 0 && (
        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 ml-3">Sections</label>
          {posterData.sections.map((section, index) => (
            <div key={section.section_id || `section-${index}`} className="mb-3 p-3 border rounded-md hover:bg-gray-50 bg-white editable-text-section">
              <div className="mb-2" data-target-id={`section_${section.section_id}_title`}>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">Section {index + 1} Title</label>
                {renderEditableField(section.section_title, `section_${section.section_id}_title`, false, `Section ${index + 1} Title`)}
              </div>
              <div className="mb-2" data-target-id={`section_${section.section_id}_content`}>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">Section {index + 1} Content</label>
                {renderEditableField(section.section_content, `section_${section.section_id}_content`, true, `Content for section ${index + 1}...`)}
              </div>

              {/* Image URL Management for this section */}
              <div className="mt-3 pt-2 pl-2 border-t border-gray-200 ml-1">
                <h5 className="text-xs font-semibold text-gray-500 mb-1">Image URLs:</h5>
                {(section.image_urls && section.image_urls.length > 0) ? (
                  <ul className="list-none pl-0 mb-2 space-y-1">
                    {section.image_urls.map((url, urlIndex) => (
                      <li key={urlIndex} className="flex justify-between items-center group bg-gray-100 p-1 rounded">
                          <span className="text-xs truncate max-w-[calc(100%-2rem)] text-blue-600 hover:underline" title={url}>
                          <a href={url} target="_blank" rel="noopener noreferrer">{url || "Invalid URL"}</a>
                        </span>
                        <button
                          onClick={() => {
                              const currentUrls = section.image_urls || [];
                              const newUrls = currentUrls.filter((_, i) => i !== urlIndex);
                              updateSectionImageUrls(section.section_id, newUrls);
                          }}
                            disabled={isLoading}
                            className="ml-2 text-red-400 hover:text-red-600 text-sm font-bold opacity-60 group-hover:opacity-100 disabled:opacity-30"
                          title="Remove URL"
                        >
                          &times;
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-gray-400 mb-2 italic">No image URLs for this section.</p>
                )}
                <div className="flex items-center mt-1">
                  <input
                    type="text"
                      placeholder="Add image URL and press Enter or click Add"
                    id={`add-url-input-${section.section_id}`}
                      disabled={isLoading}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          const inputElement = e.target as HTMLInputElement;
                           if (inputElement && inputElement.value.trim()) {
                            const currentUrls = section.image_urls || [];
                            const newUrl = inputElement.value.trim();
                            if (newUrl && !currentUrls.includes(newUrl)) {
                                updateSectionImageUrls(section.section_id, [...currentUrls, newUrl]);
                            }
                            inputElement.value = "";
                          }
                        }
                      }}
                      className="text-xs p-1 border border-gray-300 rounded-l w-full focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
                  />
                  <button
                    onClick={() => {
                      const inputElement = document.getElementById(`add-url-input-${section.section_id}`) as HTMLInputElement;
                      if (inputElement && inputElement.value.trim()) {
                           const currentUrls = section.image_urls || [];
                           const newUrl = inputElement.value.trim();
                           if (newUrl && !currentUrls.includes(newUrl)) {
                                updateSectionImageUrls(section.section_id, [...currentUrls, newUrl]);
                           }
                           inputElement.value = "";
                      }
                    }}
                      disabled={isLoading}
                      className="px-3 py-1 bg-green-500 text-white text-xs rounded-r hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50 disabled:bg-green-300"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {posterData.conclusion !== undefined && (
        <div className="mt-4 p-3 rounded-md hover:bg-gray-50 editable-text-section border-t pt-4" data-target-id="poster_conclusion">
          <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">Conclusion</label>
          {renderEditableField(posterData.conclusion, "poster_conclusion", true, "No conclusion provided.")}
        </div>
      )}
    </div>
  );
};

export default EditableTextView;
