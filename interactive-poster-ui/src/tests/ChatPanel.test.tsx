import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ChatPanel from '../components/ChatPanel';
import { AppProvider } from '../context/AppContext';

describe('ChatPanel', () => {
  it('renders the main controls heading', () => {
    // Arrange: Render the component within its context provider
    render(
      <AppProvider>
        <ChatPanel />
      </AppProvider>
    );

    // Act: Find the heading element by its role and name
    const headingElement = screen.getByRole('heading', { name: /poster controls/i });

    // Assert: Check if the element is in the document
    expect(headingElement).toBeInTheDocument();
  });
});