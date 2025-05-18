#!/usr/bin/env python3
import os
import json
import subprocess
import requests
from openai import OpenAI

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────
# Required environment variables:
#   OPENAI_API_KEY         → your OpenAI API key
#   GITHUB_TOKEN           → GitHub PAT or App token (with repo/public_repo scope)
#   GITHUB_OWNER           → e.g. "DevBotJr"
#   GITHUB_REPO            → e.g. "mcptestrepo"
#   GITHUB_ISSUE_NUMBER    → e.g. "1"
# Optional, if you want to drive a local MCP server:
#   GITHUB_MCP_CMD         → e.g. "github-mcp-server"
#   GITHUB_MCP_ARGS        → e.g. "--stdio"
# ──────────────────────────────────────────────────────────────────────────────

openai_key      = os.getenv("OPENAI_API_KEY")
gh_token        = os.getenv("LIMERICKBOT_GITHUB_TOKEN")
owner           = os.getenv("GITHUB_OWNER", "DevBotJr")
repo            = os.getenv("GITHUB_REPO", "mcptestrepo")
issue_number    = os.getenv("GITHUB_ISSUE_NUMBER", "1")
mcp_cmd         = os.getenv("GITHUB_MCP_CMD","./github-mcp-server")
mcp_args        = os.getenv("GITHUB_MCP_ARGS", "stdio --enable-command-logging --log-file mcp.log").split()

if not (openai_key and gh_token):
    raise EnvironmentError("Set OPENAI_API_KEY and GITHUB_TOKEN")

# ──────────────────────────────────────────────────────────────────────────────
# 1. GENERATE THE LIMERICK VIA OPENAI
# ──────────────────────────────────────────────────────────────────────────────
client = OpenAI(api_key=openai_key)

prompt = (
    f"Write a whimsical five-line limerick about “AI Hallucinations”.\n"
    "Each line should rhyme in AABBA pattern."
)

resp = client.chat.completions.create(
    model="o4-mini",
    messages=[{"role": "user", "content": prompt}],
)
limerick = resp.choices[0].message.content.strip()

print("Generated limerick:\n")
print(limerick)
print("\n" + "─" * 60 + "\n")

# ──────────────────────────────────────────────────────────────────────────────
# 2. DRIVE LOCAL MCP STDIO SERVER (ADVANCED)
# ──────────────────────────────────────────────────────────────────────────────
# If you have a locally installed GitHub MCP server and want to use MCP tools:
if mcp_cmd:
    # Launch the MCP server subprocess
    proc = subprocess.Popen(
        [mcp_cmd, *mcp_args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    def mcp_request(obj):
        line = json.dumps(obj)
        proc.stdin.write(line + "\n")
        proc.stdin.flush()
        # read first non-empty line as response
        while True:
            resp_line = proc.stdout.readline().strip()
            if resp_line:
                return json.loads(resp_line)

    # 1) Call the add_issue_comment tool
    comment_params = {
		"owner": "DevBotJr",
		"repo": "mcptestrepo",
		"issue_number": 1,
		"body": limerick,
		}
    call_resp = mcp_request({
	    "jsonrpc": "2.0",
	    "method": "tools/call",
	    "params": {
		    "name": "add_issue_comment",
		    "arguments": comment_params
		    },
	    "id": 2
	    })
    print("✅ Comment posted via MCP:", call_resp)

    # Clean up MCP server
    proc.stdin.close()
    proc.terminate()
    proc.wait()
