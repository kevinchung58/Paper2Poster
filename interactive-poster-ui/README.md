# Interactive Poster Generator - Frontend

This is a React-based frontend application for the Interactive Poster Generator. It allows users to interact with an LLM to create and refine poster content and see live previews.

## Features

*   Chat interface for sending prompts to the LLM.
*   Live preview of the poster, updated based on LLM responses.
*   Ability to create new poster sessions.
*   Download the final poster as a PPTX file.
*   Built with React (Vite + TypeScript) and Tailwind CSS.
*   **Theme Selection:** Choose from predefined visual themes (e.g., Default, Professional Blue, Creative Warm, Minimalist Dark) to change the overall look and feel of your poster. The selected theme affects colors, backgrounds, and fonts in the preview and the final PPTX output.
*   **Targeted Prompts:** Direct your prompts to specific parts of the poster using the "Target Prompt To:" dropdown. Options include the main title, abstract, conclusion, or the title and content of individual sections. This allows for more precise content generation and refinement by the LLM.
*   **Granular Style Overrides:** Fine-tune the appearance of specific poster elements. You can override theme settings for:
    *   Font sizes and colors for: Poster Title, Abstract, Conclusion, general Section Titles, and general Section Content.
    *   Overall slide background color.
    These overrides are applied on top of the selected theme.
*   **Direct Text Editing:** Edit poster content (titles, abstracts, section text, conclusions) directly in a dedicated "Poster Text View" area. Changes are saved and reflected in the main preview image and final PPTX.
*   **Section Image Management (URLs):** Add or remove image URLs for each poster section directly within the "Poster Text View". The backend will attempt to download and embed these images into the final PPTX.

## Setup and Running

1.  **Prerequisites:**
    *   Node.js (which includes npm) or Yarn.
    *   A running instance of the `interactive_poster_backend` service.

2.  **Installation:**
    *   Clone the repository (if applicable).
    *   Navigate to the `interactive-poster-ui` directory.
    *   Install dependencies:
        ```bash
        npm install
        # OR
        yarn install
        ```

3.  **Configuration:**
    *   The frontend needs to know the URL of the backend API. This is configured in `src/services/api.ts` in the `API_BASE_URL` constant.
    *   By default, it's set to `http://localhost:8000/api/v1`. Ensure this matches where your backend is running. The image previews also assume the backend is at `http://localhost:8000`.

4.  **Running the Frontend:**
    *   Start the development server:
        ```bash
        npm run dev
        # OR
        yarn dev
        ```
    *   This will typically open the application in your web browser (e.g., at `http://localhost:5173`).

## Key Interactions

*   **Starting a Poster:** Click "Create New Poster" (optionally provide a topic) to begin.
*   **Changing Themes:** Once a poster is active, use the "Poster Theme:" dropdown in the chat panel to select a visual theme. The preview will update to reflect your choice.
*   **Targeting LLM Prompts:** Before typing a prompt for the LLM:
    1.  Use the "Target Prompt To:" dropdown (below the theme selector) to choose which part of the poster you want the LLM to focus on (e.g., "Poster Title", "Section 1: Content").
    2.  Type your prompt in the chat input (e.g., "Rewrite this section to be more concise" or "Suggest a title for this section").
    3.  Click "Send Prompt to LLM". The LLM's response will be applied to the selected target area.
    4.  If "Entire Poster / General" is selected, the prompt is more general and may be used by the LLM to update broader aspects like the abstract, or provide general suggestions.
*   **Applying Granular Styles:**
    1.  Once a poster is active, a "Granular Style Overrides" panel will appear below the main chat/poster controls.
    2.  Use the input fields in this panel to set specific font sizes (in pt), colors (as hex codes, e.g., `#FF0000`), or a slide background color.
    3.  Changes are applied automatically shortly after you finish typing (due to debouncing).
    4.  These granular overrides will be applied on top of the currently selected theme and will be reflected in the preview and the final PPTX.
    5.  To remove an override and revert to the theme's style for a specific property, clear the input field for that property.
*   **Directly Editing Text Content:**
    1.  Below the main poster image preview, you'll find the "Poster Text View (Editable Content Area)".
    2.  This area displays the textual content of your poster (Title, Abstract, Sections, Conclusion).
    3.  Click on any text field (e.g., the current title, or the content of a section). It will transform into an editable input field or textarea.
    4.  Make your changes to the text.
    5.  To save, either click outside the field (onBlur) or press `Enter` (for single-line fields like titles). Pressing `Escape` while editing will cancel changes. (Note: For multi-line textareas, standard Enter creates a new line; saving typically occurs on blur).
    6.  Upon saving, the main poster preview image will update to reflect your direct text edits, and a confirmation message will appear in the chat log. These changes are saved directly to the backend, bypassing LLM generation for that specific edit.
*   **Managing Image URLs for Sections:**
    1.  In the "Poster Text View" for each section, below the content editing area, you will find an "Image URLs for this Section" area.
    2.  Existing image URLs (if any) will be listed with an "X" button to remove them.
    3.  To add an image, paste or type a valid, direct image URL into the input field and click the "Add" button (or press Enter).
    4.  Changes to image URLs are saved to the backend and will trigger a preview update. The final PPTX will attempt to include these images. (Note: The live preview image generated by `soffice` may not always render images from web URLs, but they should appear in the downloaded PPTX).
*   **Downloading:** Click "Generate & Download PPTX" to get the final PowerPoint file.

## Development

*   **State Management:** Uses React Context API (`src/context/AppContext.tsx`).
*   **API Calls:** Managed in `src/services/api.ts` using Axios.
*   **Components:** Located in `src/components/`.

## Dependencies

*   React (with Vite and TypeScript)
*   Tailwind CSS
*   Axios
*   (Refer to `package.json` for a full list)
