import React, { useState, useEffect } from 'react';
import { useAppContext } from '../context/AppContext';
import { PosterElementStyles, ElementStyleProperties } from '../types/posterTypes';

// Define which elements can be styled and their user-friendly labels
type StyleableElementKey = Exclude<keyof PosterElementStyles, 'slide_background'>;

const STYLABLE_ELEMENTS: Array<{ key: StyleableElementKey; label: string; props: Array<{ propKey: keyof ElementStyleProperties; label: string; type: 'text' | 'number' }> }> = [
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
    const [localOverrides, setLocalOverrides] = useState<PosterElementStyles>({});

    // Effect to sync local state when context data changes
    useEffect(() => {
        setLocalOverrides(posterData?.style_overrides || {});
    }, [posterData?.style_overrides]);

    // Effect to debounce updates to the context/API
    useEffect(() => {
        if (!posterId) return;

        const handler = setTimeout(() => {
            // Only update if there's a change from the source data to prevent loops
            if (JSON.stringify(localOverrides) !== JSON.stringify(posterData?.style_overrides || {})) {
                updateStyleOverrides(localOverrides);
            }
        }, 1000); // 1-second debounce delay

        return () => {
            clearTimeout(handler);
        };
    }, [localOverrides, posterId, posterData?.style_overrides, updateStyleOverrides]);


    const handleElementStyleChange = (
        elementKey: StyleableElementKey,
        propKey: keyof ElementStyleProperties,
        value: string
    ) => {
        const newOverrides = JSON.parse(JSON.stringify(localOverrides || {})) as PosterElementStyles;

        // Ensure the nested object exists
        if (!newOverrides[elementKey]) {
            newOverrides[elementKey] = {};
        }

        const elementStyles = newOverrides[elementKey] as ElementStyleProperties;
        const processedValue = propKey === 'font_size' ? parseInt(value, 10) : value;

        if (value === '' || (propKey === 'font_size' && isNaN(processedValue))) {
            delete elementStyles[propKey];
            // If the parent element has no more styles, remove it
            if (Object.keys(elementStyles).length === 0) {
                delete newOverrides[elementKey];
            }
        } else {
            elementStyles[propKey] = processedValue;
        }

        setLocalOverrides(newOverrides);
    };

    const handleSlideBgChange = (value: string) => {
        const newOverrides = JSON.parse(JSON.stringify(localOverrides || {})) as PosterElementStyles;
        if (value === '') {
            delete newOverrides.slide_background;
        } else {
            newOverrides.slide_background = value;
        }
        setLocalOverrides(newOverrides);
    };


    const getElementStyleValue = (elementKey: StyleableElementKey, propKey: keyof ElementStyleProperties): string => {
        const value = localOverrides?.[elementKey]?.[propKey];
        return value === undefined || value === null ? '' : String(value);
    };

    const getSlideBgValue = (): string => {
        return localOverrides?.slide_background || '';
    };

    if (!posterId || !posterData) {
        return <div className="mt-4 p-3 bg-gray-50 rounded-md text-sm text-gray-500">No active poster. Create or load a poster to enable style controls.</div>;
    }

    return (
        <div className="mt-4 p-3 border rounded-lg bg-white shadow-sm max-h-[40vh] overflow-y-auto">
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
                                value={getElementStyleValue(element.key, prop.propKey)}
                                onChange={e => handleElementStyleChange(element.key, prop.propKey, e.target.value)}
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
                        onChange={e => handleSlideBgChange(e.target.value)}
                        className="mt-1 w-full p-1 border border-gray-300 rounded-md text-xs focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="#RRGGBB"
                        disabled={isLoading}
                    />
                </label>
            </div>
            <p className="text-xs text-gray-500 italic mt-2">Changes are applied automatically with a short delay after you type.</p>
        </div>
    );
};

export default StyleControls;