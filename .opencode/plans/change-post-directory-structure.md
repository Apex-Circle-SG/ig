# Change Plan: Flatten Post Directory Structure

## Status: Ready for execution

## Description
Modify the sync_wordpress.py script to stop creating category/subcategory subdirectories and save all posts directly into the root _posts/ folder.

## Affected File
`/home/openclaw/ig/scripts/sync_wordpress.py`

## Changes Required:
1. **Remove category folder creation (lines 138-140)**
   - Delete: `folder = os.path.join(POST_DIR, *cat_path)`
   - Delete: `Path(folder).mkdir(parents=True, exist_ok=True)`

2. **Update path construction (line 144)**
   - Change from: `path = os.path.join(folder, filename)`
   - Change to:   `path = os.path.join(POST_DIR, filename)`

3. **Preserve category metadata**
   - Category information will still be kept in the markdown frontmatter (line 150)
   - Only filesystem directory structure is being changed

## Result
All posts will be saved as:
`_posts/YYYY-MM-DD-slug-name.md`

Which will be served at:
`aloycwl.github.io/ig/slug-name`

## Verification
- Existing sync state will not be affected
- Post frontmatter remains identical
- Slug naming and date prefix behavior unchanged
- All existing posts will sync correctly to the new location
