#!/usr/bin/env bash
# Syncs new rows from results.tsv → Notion CoGames Results database.
# Tracks which commits are already synced in .notion_synced_commits

REPO="$HOME/Projects/cogames-autoresearch"
NOTION_TOKEN=$(cat "$HOME/.openclaw/.secrets/notion_token" 2>/dev/null)
DB_ID="31de9256-bfef-81bf-95fd-c9f2a1b1fc91"
SYNCED_FILE="$REPO/.notion_synced_commits"

touch "$SYNCED_FILE"

tail -n +2 "$REPO/results.tsv" | while IFS=$'\t' read -r r_commit r_score r_reward r_mem r_status r_desc; do
  if grep -qF "$r_commit" "$SYNCED_FILE"; then
    continue  # already synced
  fi
  DESC_JSON=$(echo "$r_desc" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))")
  RESULT=$(curl -s -X POST "https://api.notion.com/v1/pages" \
    -H "Authorization: Bearer $NOTION_TOKEN" \
    -H "Notion-Version: 2022-06-28" \
    -H "Content-Type: application/json" \
    -d "{
      \"parent\": { \"database_id\": \"$DB_ID\" },
      \"properties\": {
        \"Description\": { \"title\": [{ \"text\": { \"content\": $DESC_JSON } }] },
        \"Commit\": { \"rich_text\": [{ \"text\": { \"content\": \"$r_commit\" } }] },
        \"Composite Score\": { \"number\": $r_score },
        \"Mean Reward\": { \"number\": $r_reward },
        \"Status\": { \"select\": { \"name\": \"$r_status\" } }
      }
    }")
  OBJ=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('object','error'))" 2>/dev/null)
  if [[ "$OBJ" == "page" ]]; then
    echo "$r_commit" >> "$SYNCED_FILE"
    echo "Synced: $r_commit | $r_score | $r_status | $r_desc"
  else
    echo "FAILED: $r_commit — $RESULT"
  fi
done
