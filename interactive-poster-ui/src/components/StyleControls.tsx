import React, { useState, useEffect, useCallback } from 'react';
import { useAppContext } from '../context/AppContext';
import { PosterElementStyles, ElementStyleProperties } from '../types/posterTypes'; // Using central types
import { debounce } from 'lodash'; // For debouncing updates

// Define which elements can be styled and their user-friendly labels
const STYLABLE_ELEMENTS: Array<{ key: keyof PosterElementStyles; label: string; props: Array<{ propKey: keyof ElementStyleProperties; label: string; type: 'text' | 'number' | 'color_picker_placeholder' }> }> = [
  { key: 'title', label: 'Poster Title', props: [
    { propKey: 'font_size', label: 'Font Size (pt)', type: 'number'},
    { propKey: 'color', label: 'Color (hex)', type: 'text'},
    { propKey: 'font_family', label: 'Font Family', type: 'text'},
  ]},
  { key: 'abstract', label: 'Abstract', props: [
    { propKey: 'font_size', label: 'Font Size (pt)', type: 'number'},
    { propKey: 'color', label: 'Color (hex)', type: 'text'},
  ]},
  { key: 'section_title', label: 'Section Titles (General)', props: [
    { propKey: 'font_size', label: 'Font Size (pt)', type: 'number'},
    { propKey: 'color', label: 'Color (hex)', type: 'text'},
  ]},
  { key: 'section_content', label: 'Section Content (General)', props: [
    { propKey: 'font_size', label: 'Font Size (pt)', type: 'number'},
    { propKey: 'color', label: 'Color (hex)', type: 'text'},
  ]},
  { key: 'conclusion', label: 'Conclusion', props: [
    { propKey: 'font_size', label: 'Font Size (pt)', type: 'number'},
    { propKey: 'color', label: 'Color (hex)', type: 'text'},
  ]},
];

const StyleControls: React.FC = () => {
  const { posterId, posterData, updateStyleOverrides, isLoading } = useAppContext();

  // Local state for form inputs, initialized from context or empty
  const [localOverrides, setLocalOverrides] = useState<PosterElementStyles>({});

  useEffect(() => {
    setLocalOverrides(posterData?.style_overrides || {});
  }, [posterData?.style_overrides]);

  // Debounced version of updateStyleOverrides from context
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const debouncedUpdate = useCallback(debounce((newOverrides: PosterElementStyles) => {
    if (posterId) {
      updateStyleOverrides(newOverrides);
    }
  }, 1000), [posterId, updateStyleOverrides]);


  const handleStyleChange = (
    elementKey: keyof PosterElementStyles,
    propKey: keyof ElementStyleProperties | 'slide_background_color', // Special case for slide_background
    value: string | number | undefined // Allow undefined to clear
  ) => {
    const newOverrides = JSON.parse(JSON.stringify(localOverrides || {})) as PosterElementStyles;

    if (propKey === 'slide_background_color') {
      newOverrides.slide_background = value as string | undefined;
    } else {
      // Ensure the element key exists
      if (!newOverrides[elementKey]) {
        (newOverrides as any)[elementKey] = {};
      }

      const typedElementKey = elementKey as Exclude<keyof PosterElementStyles, 'slide_background'>;
      const typedPropKey = propKey as keyof ElementStyleProperties;

      if (newOverrides[typedElementKey]) { // Type guard
        if (value === '' || value === undefined) {
          delete (newOverrides[typedElementKey] as any)![typedPropKey]; // Remove property if value is empty/undefined
          if (Object.keys(newOverrides[typedElementKey]!).length === 0) {
            delete newOverrides[typedElementKey]; // Remove element key if it has no properties
          }
        } else {
          (newOverrides[typedElementKey] as any)![typedPropKey] =
            (typedPropKey === 'font_size' && typeof value === 'string') ? parseInt(value, 10) : value;
        }
      }
    }

    setLocalOverrides(newOverrides);
    debouncedUpdate(newOverrides); // Call debounced update
  };

  const getStyleValue = (elementKey: keyof PosterElementStyles, propKey: keyof ElementStyleProperties): string => {
    const typedElementKey = elementKey as Exclude<keyof PosterElementStyles, 'slide_background'>;
    const value = localOverrides?.[typedElementKey]?.[propKey];
    return value === undefined || value === null ? '' : String(value);
  };

  const getSlideBgValue = (): string => {
    return localOverrides?.slide_background || '';
  };

  if (!posterId || !posterData) {
    return <div className="mt-4 p-3 bg-gray-50 rounded-md text-sm text-gray-500">No active poster. Create or load a poster to enable style controls.</div>;
  }

  return (
    <div className="mt-4 p-3 border rounded-lg bg-white shadow-sm max-h-[40vh] overflow-y-auto"> {/* Added max-h and overflow */}
      <h3 className="text-lg font-semibold mb-3 text-gray-700 sticky top-0 bg-white py-2 z-10 border-b -mx-3 px-3">
        Granular Style Overrides
      </h3>

      {STYLABLE_ELEMENTS.map(element => (
        <div key={element.key} className="mb-3 p-2 border rounded-md bg-gray-50">
          <h4 className="font-medium text-md mb-2 text-gray-600">{element.label}</h4>
          {element.props.map(prop => (
            <label key={prop.propKey} className="block text-xs text-gray-700 mb-2">
              {prop.label}:
              <input
                type={prop.type === 'number' ? 'number' : 'text'}
                value={getStyleValue(element.key as any, prop.propKey)}
                onChange={e => handleStyleChange(element.key as any, prop.propKey, e.target.value)}
                className="mt-1 w-full p-1 border border-gray-300 rounded-md text-xs focus:ring-indigo-500 focus:border-indigo-500"
                placeholder={prop.propKey === 'color' ? '#RRGGBB' : prop.propKey === 'font_family' ? 'e.g., Arial' : ''}
                disabled={isLoading}
              />
            </label>
          ))}
        </div>
      ))}

      <div className="mb-3 p-2 border rounded-md bg-gray-50">
        <h4 className="font-medium text-md mb-2 text-gray-600">General Slide</h4>
        <label className="block text-xs text-gray-700 mb-2">
          Background Color (hex):
          <input
            type="text"
            value={getSlideBgValue()}
            onChange={e => handleStyleChange('slide_background' as any, 'slide_background_color', e.target.value)}
            className="mt-1 w-full p-1 border border-gray-300 rounded-md text-xs focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="#RRGGBB"
            disabled={isLoading}
          />
        </label>
      </div>

      {/* No explicit "Apply Styles" button; using debounced updates on change.
          An explicit button can be added if preferred over debouncing. */}
      {/* <button
        onClick={() => updateStyleOverrides(localOverrides)}
        disabled={isLoading}
        className="mt-3 w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
      >
        Apply All Style Overrides
      </button> */}
      <p className="text-xs text-gray-500 italic mt-2">Changes are applied automatically with a short delay after you type.</p>
    </div>
  );
};

export default StyleControls;
