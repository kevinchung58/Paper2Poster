import React, { useState } from 'react'; // Removed useEffect for now, will add back if needed for focusing
import { useAppContext } from '../context/AppContext';

const EditableTextView = () => {
  const { posterData, isLoading, directUpdateElement } = useAppContext(); // Add directUpdateElement

  const [editingTargetId, setEditingTargetId] = useState<string | null>(null);
  const [editingValue, setEditingValue] = useState<string>("");
  const [originalValue, setOriginalValue] = useState<string>(""); // Store original value on edit start

  const handleEditClick = (targetId: string, currentValue: string | undefined | null) => {
    setEditingTargetId(targetId);
    const cv = currentValue ?? "";
    setEditingValue(cv);
    setOriginalValue(cv); // Store original value when starting edit
  };

  const handleBlurSave = async () => { // Make async
    if (editingTargetId && editingValue !== originalValue) {
      // Only call update if value actually changed
      await directUpdateElement(editingTargetId, editingValue);
    }
    setEditingTargetId(null);
  };

  // Handle Enter key for single-line inputs, Shift+Enter for textarea is default
  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !(event.target instanceof HTMLTextAreaElement && event.shiftKey)) {
      event.preventDefault();
      handleBlurSave(); // Trigger save/exit edit mode
    } else if (event.key === 'Escape') {
      setEditingTargetId(null); // Cancel editing
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

  const renderText = (text: string | undefined | null, defaultText: string = "Click to edit...") => {
    return text || defaultText;
  };

  const renderEditableField = (
    currentValue: string | undefined | null,
    targetId: string,
    label: string,
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
          className={`${targetId === 'poster_title' ? 'text-2xl font-bold' : 'text-lg font-semibold'} p-1 border border-blue-500 rounded w-full shadow-sm`}
        />
      );
    }
    return (
      <p
        className={`${
          targetId === 'poster_title' ? 'text-2xl font-bold' :
          targetId.endsWith('_title') ? 'text-lg font-semibold' : 'text-md'
        } editable-content p-1 border border-transparent hover:border-gray-300 rounded cursor-pointer whitespace-pre-wrap`}
        onClick={() => handleEditClick(targetId, currentValue)}
      >
        {renderText(currentValue, defaultPlaceholder)}
      </p>
    );
  };


  return (
    <div className="my-6 p-4 md:p-6 border rounded-lg bg-white shadow-md">
      <h3 className="text-xl font-semibold mb-4 border-b pb-2 text-gray-700">
        Poster Content (Click text to edit)
      </h3>

      {/* Poster Title */}
      <div className="mb-4 p-3 rounded-md hover:bg-gray-50 editable-text-section" data-target-id="poster_title">
        <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">Title</label>
        {renderEditableField(posterData.title, "poster_title", "Title", false, "Untitled Poster")}
      </div>

      {/* Poster Abstract */}
      {posterData.abstract !== undefined && (
        <div className="mb-4 p-3 rounded-md hover:bg-gray-50 editable-text-section" data-target-id="poster_abstract">
          <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">Abstract</label>
          {renderEditableField(posterData.abstract, "poster_abstract", "Abstract", true, "No abstract provided.")}
        </div>
      )}

      {/* Sections */}
      {posterData.sections && posterData.sections.length > 0 && (
        <div className="mb-4">
             <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 ml-3">Sections</label>
            {posterData.sections.map((section, index) => (
            <div key={section.section_id || `section-${index}`} className="mb-3 p-3 border rounded-md hover:bg-gray-50 bg-white editable-text-section">
                <div className="mb-2" data-target-id={`section_${section.section_id}_title`}>
                    <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">Section {index + 1} Title</label>
                    {renderEditableField(section.section_title, `section_${section.section_id}_title`, `Section ${index + 1} Title`, false, `Section ${index + 1} Title`)}
                </div>
                <div data-target-id={`section_${section.section_id}_content`}>
                    <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">Section {index + 1} Content</label>
                    {renderEditableField(section.section_content, `section_${section.section_id}_content`, `Section ${index + 1} Content`, true, `Content for section ${index + 1}...`)}
                </div>
            </div>
            ))}
        </div>
      )}

      {/* Poster Conclusion */}
      {posterData.conclusion !== undefined && (
        <div className="mt-4 p-3 rounded-md hover:bg-gray-50 editable-text-section border-t pt-4" data-target-id="poster_conclusion">
          <label className="block text-xs font-medium text-gray-500 uppercase tracking-wider">Conclusion</label>
          {renderEditableField(posterData.conclusion, "poster_conclusion", "Conclusion", true, "No conclusion provided.")}
        </div>
      )}
    </div>
  );
};

export default EditableTextView;
