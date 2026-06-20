# UI Redesign Plan

## Objective
The current UI feels cluttered, clunky, and uses inconsistent styles (heavy serif fonts, gradient backgrounds, yellow-tinted inputs, drop shadows). The goal is to completely revamp the design into a highly minimalist, modern, and premium aesthetic without overengineering or adding new dependencies (like Tailwind). We will stick to vanilla CSS.

## Key Changes
1. **Typography**:
   - Remove `Georgia` serif font.
   - Use a modern `system-ui` sans-serif stack (e.g., `Inter`, `-apple-system`, `BlinkMacSystemFont`, `Roboto`).
   - Use font weights (e.g., `400`, `500`, `600`) to establish hierarchy rather than massive font sizes.

2. **Color Palette**:
   - **Background**: Switch from yellowish radial gradients to a clean, crisp off-white (`#fafafa`) or pure white (`#ffffff`).
   - **Text**: Deep, premium dark gray/black (`#111827`, `#374151`) for better readability.
   - **Accent**: Replace the heavy teal/orange with a minimalist, high-contrast accent color (e.g., solid black `#000000` or a deep indigo/blue `#2563eb`).
   - **Borders/Inputs**: Soft gray borders (`#e5e7eb`) with transparent or white backgrounds. Remove the yellowish tint from inputs.

3. **Layout & Elements**:
   - **Login Page**: Center the content vertically and horizontally. Make the form a sleek, simple card with subtle borders instead of heavy shadows.
   - **App Layout**: Clean up the `workspace` grid.
     - **Sidebar**: Remove the bulky card look. Make it feel like a seamless part of the layout with a subtle right border.
     - **Active Flow (Main Content)**: Remove the bulky "Step Cards" and orange gradient number bubbles. Use elegant typography for step headings, sleek input fields, and flat, simple buttons.
   - **Shadows**: Remove heavy `box-shadow` styles. Use extremely subtle shadows only where depth is absolutely necessary, or rely on borders.

4. **Implementation Steps**:
   - **Step 1**: Modify `frontend/src/styles.css` to update CSS variables (colors), reset typography, and strip out gradients/shadows.
   - **Step 2**: Update layout grids and padding in `styles.css` for `.app`, `.hero`, `.workspace`, and `.step-card` to match the minimalist vibe.
   - **Step 3**: Minor adjustments to class names or HTML structure in `frontend/src/App.tsx` if necessary to support the cleaner layout.

## Review Request
Please approve this plan, and I will proceed with the CSS/TSX refactor in `Execute` mode.
