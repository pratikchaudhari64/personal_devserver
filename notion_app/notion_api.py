import os
from notion_client import Client

from pprint import pprint
from dotenv import load_dotenv

import re

load_dotenv()

SECRET_PATH = "/run/secrets/notion_api_key"

def load_notion_api_key():
    """Reads the API key from the Docker secret file."""
    if os.path.exists(SECRET_PATH):
        with open(SECRET_PATH, 'r') as f:
            # .strip() is important to remove any trailing newline characters
            return f.read().strip()
    else:
        # Fallback for local development if not using Docker secrets
        print("Warning: Notion secret file not found. Falling back to environment variable.")
        return os.environ.get("NOTION_TOKEN")

NOTION_API_KEY = load_notion_api_key()

def get_markdown(page_number_dummy_input):

    notion_token = os.getenv('NOTION_TOKEN')
    if notion_token is None:
        raise Exception("NOTION_TOKEN environment variable not found")
    notion = Client(auth=os.environ["NOTION_TOKEN"])


    # --- Helper function to extract page title ---
    def extract_page_title(page_object: dict) -> str:
        """
        Extracts the title from a Notion page object,
        handling both database pages and standalone pages.
        """
        if page_object["object"] == "page":
            properties = page_object.get("properties")
            if properties:
                # Iterate through properties to find the 'title' type
                for prop_name, prop_value in properties.items():
                    if prop_value.get("type") == "title":
                        # The title content is an array of rich text objects
                        title_array = prop_value.get("title", [])
                        if title_array:
                            # Concatenate plain_text from all rich text objects
                            return "".join([text.get("plain_text", "") for text in title_array if text.get("type") == "text"])
                        else:
                            return "Untitled Page (No Title Text)"
                # If no 'title' type property is found (e.g., standalone page without explicit title property)
                # This case is less common for search results, but good for robustness
                # For standalone pages, the title might sometimes be directly at the top level
                # of the page object when retrieved directly, but in search results,
                # it's always within 'properties' for consistency.
                pass # Fall through to default if no title property found
            
            # Fallback if properties or title is missing for some reason
            return "Untitled Page (Properties Missing)"
        
        elif page_object["object"] == "database":
            # Databases have their title directly on the top level, as an array of rich text
            title_array = page_object.get("title", [])
            if title_array:
                return "".join([text.get("plain_text", "") for text in title_array if text.get("type") == "text"])
            else:
                return "Untitled Database"
        
        # Fallback for unexpected object types (shouldn't happen with filter)
        return "Unknown Object (No Title)"

    
    
    # --- Pagination and Filtering Logic ---

    def get_all_pages():

        all_pages = []
        next_cursor = None
        has_more = True

        print("Fetching all page objects from Notion workspace (this may take a moment for large workspaces)...")

        try:
            while has_more:
                # Define the search parameters for the current request
                search_params = {
                    # Filter to retrieve only 'page' objects
                    "filter": {
                        "property": "object",
                        "value": "page"
                    },
                    
                }

                # If a next_cursor exists from a previous request, add it to the parameters
                if next_cursor:
                    search_params["start_cursor"] = next_cursor

                # Make the search API call
                response = notion.search(**search_params)

                # Extend the list of all pages with the results from the current response
                all_pages.extend(response["results"])

                # Update has_more and next_cursor for the next iteration
                has_more = response.get("has_more", False)
                next_cursor = response.get("next_cursor")

                # Optional: Print progress
                print(f"  Fetched {len(response['results'])} pages. Total so far: {len(all_pages)}")

                return all_pages

        except Exception as e:
            print(f"An error occurred during Notion API interaction: {e}")
            
    # --- Process and Display Results ---

    all_pages = get_all_pages()

    def get_log_pages():

        log_pages = []

        if all_pages:
            try:
                for i, page in enumerate(all_pages):
                    try:
                        # get_page_title is a helper from notion_client.helpers
                        # It safely extracts the title from various page property structures
                        title = extract_page_title(page)
                        # print(f"{i+1}. Title: '{title}', ID: {page['id']}")
                        log_page = {}
                        if (re.search(r'\blog\b', title) is not None) and (page['properties']['Date']['date'] is not None):
                            log_page['title'] = title
                            log_page['id'] = page['id']
                            log_page['date'] = page['properties']['Date']['date']

                            log_pages.append(log_page)

                    except Exception as e:
                        print(f"{i+1}. Could not get title for page ID: {page['id']} - Error: {e}")
                        print(f"   Raw page object: {page}")
            except:
                print("no pages on 'logs' found")
            
            return log_pages

        else:
            print("No pages found. Ensure your integration has access to pages in Notion.")    

        pass

    log_title_pages = get_log_pages()


    pg_id = log_title_pages[page_number_dummy_input]['id']
    # --- Helper functions to process Notion rich_text and blocks ---

    def convert_rich_text_to_markdown(rich_text_array: list) -> str:
        """
        Converts a Notion rich_text array into a Markdown-formatted string.
        """
        if not rich_text_array:
            return ""

        markdown_parts = []
        for text_object in rich_text_array:
            plain_text = text_object.get("plain_text", "")
            annotations = text_object.get("annotations", {})
            href = text_object.get("href")

            formatted_text = plain_text

            # Apply annotations
            if annotations.get("bold"):
                formatted_text = f"**{formatted_text}**"
            if annotations.get("italic"):
                formatted_text = f"*{formatted_text}*"
            if annotations.get("strikethrough"):
                formatted_text = f"~~{formatted_text}~~"
            if annotations.get("underline"):
                # Markdown doesn't have native underline, can use HTML if targeting HTML,
                # but for pure Markdown, we'll just skip it or denote it.
                formatted_text = f"__{formatted_text}__" # Common markdown extension for underline
            if annotations.get("code"):
                formatted_text = f"`{formatted_text}`"
            
            # Apply link
            if href:
                formatted_text = f"[{formatted_text}]({href})"
            
            markdown_parts.append(formatted_text)
        
        return "".join(markdown_parts)

    def get_all_block_children(block_id: str, client: Client, indent_level: int = 0) -> list:
        """
        Recursively retrieves all child blocks of a given block ID.
        Adds an 'indent_level' property to each block for structural awareness.
        """
        all_blocks = []
        next_cursor = None
        has_more = True

        while has_more:
            try:
                response = client.blocks.children.list(
                    block_id=block_id,
                    start_cursor=next_cursor,
                    page_size=100 # Max results per request
                )
                
                for block in response["results"]:
                    block["indent_level"] = indent_level # Add current indent level
                    all_blocks.append(block)

                has_more = response.get("has_more", False)
                next_cursor = response.get("next_cursor")
            except Exception as e:
                print(f"Error fetching children for block {block_id}: {e}")
                break # Stop if there's an error in fetching
        
        # Recursively get children of children if they exist
        for block in all_blocks:
            # Exclude 'child_page' and 'child_database' as their content is in a separate tree.
            # If you wanted to include their content, you'd call this function on their 'id'
            # and integrate the results appropriately, potentially by fetching the actual page.
            if block.get("has_children") and block["type"] not in ["child_page", "child_database", "synced_block"]:
                block["children"] = get_all_block_children(block["id"], client, indent_level + 1)
            # Handle linked synced blocks (original content)
            elif block["type"] == "synced_block" and block["synced_block"].get("synced_from") is None:
                # This is the original synced block, retrieve its content
                block["children"] = get_all_block_children(block["id"], client, indent_level + 1)
        
        return all_blocks
    
    markdown_content_blob = []
    PAGE_ID_TO_RETRIEVE = pg_id
    print(f"Retrieving and converting content for page ID: {PAGE_ID_TO_RETRIEVE}")
    
    # try-except block converts content to markdown for whatever page ID. Need to convert to a function
    try:
        # Get all blocks (and their nested children) for the page
        blocks = get_all_block_children(PAGE_ID_TO_RETRIEVE, notion)
        
        # Helper to process blocks recursively and append to markdown_content_blob
        def process_blocks_to_markdown(block_list: list):
            for block in block_list:
                block_type = block["type"]
                indent = "  " * block.get("indent_level", 0) # Use the stored indent level
                
                # Handle different block types and their text content
                if block_type in ["paragraph", "heading_1", "heading_2", "heading_3",
                                  "bulleted_list_item", "numbered_list_item", "to_do",
                                  "quote", "callout", "toggle", "code_block", "divider"]: # 'code_block' is the new type name
                    
                    block_data = block.get(block_type)
                    if block_data and block_data.get("rich_text"):
                        text_md = convert_rich_text_to_markdown(block_data["rich_text"])
                    elif block_type == "to_do": # To-do items have a 'checked' property
                         checked_status = "[x] " if block_data.get("checked") else "[ ] "
                         text_md = checked_status + convert_rich_text_to_markdown(block_data["rich_text"])
                    elif block_type == "divider":
                        text_md = "---"
                    else:
                        text_md = ""

                    # Add Markdown specific formatting for headings and lists
                    if block_type == "heading_1":
                        markdown_content_blob.append(f"\n{indent}# {text_md}\n")
                    elif block_type == "heading_2":
                        markdown_content_blob.append(f"\n{indent}## {text_md}\n")
                    elif block_type == "heading_3":
                        markdown_content_blob.append(f"\n{indent}### {text_md}\n")
                    elif block_type == "bulleted_list_item":
                        markdown_content_blob.append(f"{indent}- {text_md}\n")
                    elif block_type == "numbered_list_item":
                        # This would require tracking numbering, which is complex. For simplicity, just a list item.
                        # For true numbering, you'd need to manage state per list.
                        markdown_content_blob.append(f"{indent}1. {text_md}\n") # Simplified
                    elif block_type == "quote":
                        markdown_content_blob.append(f"\n{indent}> {text_md}\n")
                    elif block_type == "callout":
                        # Callouts often have an icon and content. Just taking content here.
                        icon = block_data.get("icon", {}).get("emoji", "💡")
                        markdown_content_blob.append(f"\n{indent}{icon} {text_md}\n")
                    elif block_type == "toggle":
                        markdown_content_blob.append(f"\n{indent}<details><summary>{text_md}</summary>\n")
                        # Toggle content will be in children
                        if block.get("children"):
                            process_blocks_to_markdown(block["children"])
                        markdown_content_blob.append(f"{indent}</details>\n")
                    elif block_type == "code_block": # Use code_block for API version 2022-06-28 or newer
                        if block_data.get("rich_text"):
                            code_content = convert_rich_text_to_markdown(block_data["rich_text"])
                            language = block_data.get("language", "plaintext")
                            markdown_content_blob.append(f"\n{indent}```{language}\n{code_content}\n{indent}```\n")
                    else: # Default for paragraph and others
                        markdown_content_blob.append(f"{indent}{text_md}\n")

                # Handle blocks that don't have rich_text but might contribute to the "blob"
                elif block_type == "image":
                    url = block["image"].get("file", {}).get("url") or block["image"].get("external", {}).get("url")
                    caption = convert_rich_text_to_markdown(block["image"].get("caption", []))
                    if url:
                        markdown_content_blob.append(f"\n{indent}![{caption if caption else 'image'}]({url})\n")
                elif block_type == "bookmark":
                    url = block["bookmark"].get("url")
                    caption = convert_rich_text_to_markdown(block["bookmark"].get("caption", []))
                    if url:
                        markdown_content_blob.append(f"\n{indent}[Bookmark: {caption if caption else url}]({url})\n")
                elif block_type == "child_page":
                    # This block type refers to another page. You might just want its title and ID.
                    markdown_content_blob.append(f"\n{indent}## [Child Page: {block['child_page'].get('title', 'Untitled Child Page')}]({block['id']})\n")
                elif block_type == "unsupported":
                    markdown_content_blob.append(f"{indent}[Unsupported Block Type]\n")
                elif block_type == "table":
                    # Tables are complex. You'd fetch rows using blocks.children.list for the table_id
                    # and format them as Markdown tables. This is a placeholder.
                    markdown_content_blob.append(f"{indent}[Table Block - Requires further processing]\n")
                elif block_type == "column_list" or block_type == "column":
                    # Column lists and columns are containers. Their content is in their children.
                    # We process their children if available, adding indentation.
                    if block.get("children"):
                        # No direct text from column_list/column block itself, just process children
                        pass # Children will be processed below

                # Process children of container blocks (like columns, toggle, synced_block original)
                if block.get("has_children") and block.get("children"):
                    if block_type not in ["toggle"]: # Handled toggle's children within its formatting
                        process_blocks_to_markdown(block["children"]) # Recursively process nested content

        # Start the recursive processing from the top-level blocks
        process_blocks_to_markdown(blocks)

    except Exception as e:
        print(f"An error occurred during content retrieval: {e}")
        print("Please ensure:")
        print(f"- The PAGE_ID_TO_RETRIEVE ('{PAGE_ID_TO_RETRIEVE}') is correct.")
        print("- Your Notion integration has 'Read content' capabilities enabled.")
        print("- Your integration has been invited to the specific page in Notion (Share -> Add people, emails, groups, or integrations).")

    final_page_content_markdown = "".join(markdown_content_blob)
    print("\n--- Retrieved Page Body Content in Markdown ---")
    # print(final_page_content_markdown)

    return final_page_content_markdown




if __name__ == "__main__":
    res = get_markdown(page_number_dummy_input=0)
    print(res)