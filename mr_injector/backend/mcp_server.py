import sys
import os
import traceback
import requests
from typing import Any, List, Dict
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv


# Load environment variables
load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')


def fetch_pr_changes(repo_owner: str, repo_name: str, pr_number: int) -> list:
    """Fetch changes from a GitHub pull request.

    Args:
        repo_owner: The owner of the GitHub repository
        repo_name: The name of the GitHub repository
        pr_number: The number of the pull request to analyze

    Returns:
        A list of file changes with detailed information about each change
    """
    print(f" Fetching PR changes for {repo_owner}/{repo_name}#{pr_number}")

    # Fetch PR details
    pr_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
    files_url = f"{pr_url}/files"
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}

    try:
        # Get PR metadata
        pr_response = requests.get(pr_url, headers=headers)
        pr_response.raise_for_status()
        pr_data = pr_response.json()

        # Get file changes
        files_response = requests.get(files_url, headers=headers)
        files_response.raise_for_status()
        files_data = files_response.json()

        # Combine PR metadata with file changes
        changes = []
        for file in files_data:
            change = {
                'filename': file['filename'],
                'status': file['status'],  # added, modified, removed
                'additions': file['additions'],
                'deletions': file['deletions'],
                'changes': file['changes'],
                'patch': file.get('patch', ''),  # The actual diff
                'raw_url': file.get('raw_url', ''),
                'contents_url': file.get('contents_url', '')
            }
            changes.append(change)

        # Add PR metadata
        pr_info = {
            'title': pr_data['title'],
            'description': pr_data['body'],
            'author': pr_data['user']['login'],
            'created_at': pr_data['created_at'],
            'updated_at': pr_data['updated_at'],
            'state': pr_data['state'],
            'total_changes': len(changes),
            'changes': changes
        }

        print(f"Successfully fetched {len(changes)} changes")
        return pr_info

    except Exception as e:
        print(f"Error fetching PR changes: {str(e)}")
        traceback.print_exc()
        return None



class PRAnalyzer:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Initialize MCP Server
        self.mcp = FastMCP("github_pr_analysis")
        print("MCP Server initialized", file=sys.stderr)


        # Register MCP tools
        self._register_tools()

    def _register_tools(self):
        """Register MCP tools for PR analysis."""

        @self.mcp.tool()
        async def fetch_pr(repo_owner: str, repo_name: str, pr_number: int) -> Dict[str, Any]:
            """Fetch changes from a GitHub pull request."""
            print(f"Fetching PR #{pr_number} from {repo_owner}/{repo_name}", file=sys.stderr)
            try:
                pr_info = fetch_pr_changes(repo_owner, repo_name, pr_number)
                if pr_info is None:
                    print("No changes returned from fetch_pr_changes", file=sys.stderr)
                    return {}
                print(f"Successfully fetched PR information", file=sys.stderr)
                return pr_info
            except Exception as e:
                print(f"Error fetching PR: {str(e)}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                return {}

    def run(self):
        """Start the MCP server."""
        try:
            print("Running MCP Server for GitHub PR Analysis...", file=sys.stderr)
            self.mcp.run(transport="stdio")
        except Exception as e:
            print(f"Fatal Error in MCP Server: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    analyzer = PRAnalyzer()
    analyzer.run()