# E2E Test: Enhanced Drop Zone Functionality

Test the enhanced drag-and-drop functionality that allows users to drop files directly onto the query section and tables section.

## User Story

As a user  
I want to drag and drop files directly onto the main interface areas  
So that I can quickly upload data without having to open the upload modal first

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state showing both query section and tables section
3. **Verify** the page title is "Natural Language SQL Interface"
4. **Verify** core sections are present:
   - Query section with textarea
   - Tables section with "Available Tables" heading

### Test Query Section Drop Zone

5. Load a test CSV file into the browser automation tool
6. Drag the CSV file over the query section
7. **Verify** drop overlay appears with "Drop to create table" text
8. Take a screenshot showing the drop overlay on query section
9. Drop the file onto the query section
10. **Verify** file upload processes successfully
11. **Verify** new table appears in the Available Tables section
12. Take a screenshot showing the uploaded table in the tables list

### Test Tables Section Drop Zone

13. Load a second test CSV file
14. Drag the CSV file over the tables section
15. **Verify** drop overlay appears with "Drop to create table" text
16. Take a screenshot showing the drop overlay on tables section
17. Drop the file onto the tables section
18. **Verify** file upload processes successfully
19. **Verify** second table appears in the Available Tables section
20. Take a screenshot showing both tables in the tables list

### Test Original Upload Modal Still Works

21. Click the "Upload" button
22. **Verify** upload modal appears with drop zone
23. Take a screenshot of the upload modal
24. Click "Cancel" to close modal

### Test Invalid File Type Handling

25. Load a non-supported file (e.g., .txt file)
26. Drag over query section
27. Drop the file
28. **Verify** error message appears indicating unsupported file type
29. Take a screenshot of the error message

## Success Criteria
- Drop overlays appear when dragging files over query and tables sections
- Drop overlays display "Drop to create table" messaging
- Files can be successfully dropped and uploaded from both areas
- Tables appear in the Available Tables section after upload
- Original upload modal functionality remains intact
- Proper error handling for invalid file types
- Visual feedback is smooth and non-intrusive
- At least 6 screenshots are captured